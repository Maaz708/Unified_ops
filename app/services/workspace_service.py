# app/services/workspace_service.py
from __future__ import annotations

from typing import List, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, exists, func

from app.core.security import hash_password  # you should implement this
from app.models.workspace import Workspace, WorkspaceStatus
from app.models.users import StaffUser, StaffRole
from app.models.booking_type import BookingType
from app.models.availability_slot import AvailabilitySlot
from app.models.workspace_email_config import WorkspaceEmailConfig, EmailProvider
from app.models.event_log import EventLog, ActorType
from app.schemas.workspace import (
    WorkspaceOnboardingRequest,
    WorkspaceOnboardingResponse,
    WorkspaceSummary,
    OnboardingValidationStatus,
)


class WorkspaceOnboardingService:
    def __init__(self, db: Session):
        self.db = db

    # -------- Public API --------

    def onboard_workspace(
        self, payload: WorkspaceOnboardingRequest
    ) -> WorkspaceOnboardingResponse:
        # Basic sanity checks
        if not payload.booking_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one booking type is required.",
            )
        if not payload.availability:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one availability slot is required.",
            )

        # Ensure owner email is not already used in this workspace name context (optional)
        # We allow same email across workspaces, but not same name+email combo for clarity.

        workspace = Workspace(
            name=payload.workspace_name,
            status=WorkspaceStatus.draft,
        )
        self.db.add(workspace)
        self.db.flush()  # get workspace.id

        owner = self._create_owner_user(workspace, payload)
        self._connect_email_provider(workspace, payload)
        self._create_booking_types(workspace, payload)
        self._define_availability(workspace, payload)

        # Validation & activation decision
        validation = self._evaluate_activation_requirements(workspace)

        if validation.can_activate:
            workspace.status = WorkspaceStatus.active
            self._log_event(
                workspace,
                event_type="workspace.activated",
                actor_type=ActorType.system,
                payload={},
            )
        else:
            workspace.status = WorkspaceStatus.pending_validation

        self.db.commit()
        self.db.refresh(workspace)
        self.db.refresh(owner)

        return WorkspaceOnboardingResponse(
            workspace=WorkspaceSummary.model_validate(workspace),
            owner_id=str(owner.id),
            validation=validation,
        )

    # -------- Internal helpers --------

    def _create_owner_user(
        self, workspace: Workspace, payload: WorkspaceOnboardingRequest
    ) -> StaffUser:
        owner_data = payload.owner

        # Prevent duplicate owner email within this workspace
        existing = self.db.scalar(
            select(StaffUser).where(
                StaffUser.workspace_id == workspace.id,
                StaffUser.email == owner_data.email,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owner email already exists in this workspace.",
            )

        owner = StaffUser(
            workspace_id=workspace.id,
            email=owner_data.email,
            full_name=owner_data.full_name,
            hashed_password=hash_password(owner_data.password),
            role=StaffRole.owner,
            is_active=True,
        )
        self.db.add(owner)
        self.db.flush()

        workspace.owner_id = owner.id

        self._log_event(
            workspace,
            event_type="workspace.owner_created",
            actor_type=ActorType.staff,
            actor_id=str(owner.id),
            payload={"email": owner.email},
        )
        return owner

    def _connect_email_provider(
        self, workspace: Workspace, payload: WorkspaceOnboardingRequest
    ) -> WorkspaceEmailConfig:
        cfg = payload.email_provider

        email_cfg = WorkspaceEmailConfig(
            workspace_id=workspace.id,
            provider=cfg.provider or EmailProvider.resend,
            from_email=cfg.from_email,
            from_name=cfg.from_name,
            api_key_alias=cfg.api_key_alias,
            is_active=True,
        )
        self.db.add(email_cfg)
        self.db.flush()

        self._log_event(
            workspace,
            event_type="workspace.email_provider_connected",
            actor_type=ActorType.system,
            payload={
                "provider": email_cfg.provider.value,
                "from_email": email_cfg.from_email,
            },
        )
        return email_cfg

    def _create_booking_types(
        self, workspace: Workspace, payload: WorkspaceOnboardingRequest
    ) -> List[BookingType]:
        created: List[BookingType] = []
        for bt in payload.booking_types:
            # Enforce unique slug per workspace
            exists_slug = self.db.scalar(
                select(exists().where(
                    BookingType.workspace_id == workspace.id,
                    BookingType.slug == bt.slug,
                    BookingType.is_deleted.is_(False),
                ))
            )
            if exists_slug:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Booking type slug '{bt.slug}' already exists.",
                )

            bt_row = BookingType(
                workspace_id=workspace.id,
                name=bt.name,
                slug=bt.slug,
                description=bt.description,
                duration_minutes=bt.duration_minutes,
            )
            self.db.add(bt_row)
            created.append(bt_row)

        self.db.flush()

        self._log_event(
            workspace,
            event_type="workspace.booking_types_created",
            actor_type=ActorType.system,
            payload={"count": len(created)},
        )
        return created

    def _define_availability(
        self, workspace: Workspace, payload: WorkspaceOnboardingRequest
    ) -> List[AvailabilitySlot]:
        # Map slug -> BookingType.id for this workspace to enforce isolation
        booking_types = self.db.scalars(
            select(BookingType).where(
                BookingType.workspace_id == workspace.id,
                BookingType.is_deleted.is_(False),
            )
        ).all()
        bt_by_slug = {bt.slug: bt for bt in booking_types}

        # Map staff email -> StaffUser.id in this workspace
        staff_by_email = {
            u.email: u
            for u in self.db.scalars(
                select(StaffUser).where(
                    StaffUser.workspace_id == workspace.id,
                    StaffUser.is_deleted.is_(False),
                )
            ).all()
        }

        slots: List[AvailabilitySlot] = []

        for slot in payload.availability:
            bt = bt_by_slug.get(slot.booking_type_slug)
            if not bt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown booking_type_slug '{slot.booking_type_slug}' for this workspace.",
                )

            staff_user_id = None
            if slot.staff_email:
                staff = staff_by_email.get(slot.staff_email)
                if not staff:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unknown staff_email '{slot.staff_email}' for this workspace.",
                    )
                staff_user_id = staff.id

            if slot.end_at <= slot.start_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Availability slot end_at must be after start_at.",
                )

            av = AvailabilitySlot(
                workspace_id=workspace.id,
                booking_type_id=bt.id,
                staff_user_id=staff_user_id,
                start_at=slot.start_at,
                end_at=slot.end_at,
            )
            self.db.add(av)
            slots.append(av)

        self.db.flush()

        self._log_event(
            workspace,
            event_type="workspace.availability_defined",
            actor_type=ActorType.system,
            payload={"count": len(slots)},
        )
        return slots

    # -------- Activation / validation --------

    def _evaluate_activation_requirements(
        self, workspace: Workspace
    ) -> OnboardingValidationStatus:
        ws_id = workspace.id

        # Communication channel: active email config
        email_connected = bool(
            self.db.scalar(
                select(func.count()).select_from(WorkspaceEmailConfig).where(
                    WorkspaceEmailConfig.workspace_id == ws_id,
                    WorkspaceEmailConfig.is_active.is_(True),
                )
            )
        )

        has_booking_types = bool(
            self.db.scalar(
                select(func.count()).select_from(BookingType).where(
                    BookingType.workspace_id == ws_id,
                    BookingType.is_deleted.is_(False),
                )
            )
        )

        has_availability = bool(
            self.db.scalar(
                select(func.count()).select_from(AvailabilitySlot).where(
                    AvailabilitySlot.workspace_id == ws_id,
                )
            )
        )

        reasons: List[str] = []
        if not email_connected:
            reasons.append("EMAIL_PROVIDER_NOT_CONNECTED")
        if not has_booking_types:
            reasons.append("NO_BOOKING_TYPES")
        if not has_availability:
            reasons.append("NO_AVAILABILITY_DEFINED")

        can_activate = not reasons

        # Log validation check
        self._log_event(
            workspace,
            event_type="workspace.validation_checked",
            actor_type=ActorType.system,
            payload={
                "email_connected": email_connected,
                "has_booking_types": has_booking_types,
                "has_availability": has_availability,
                "can_activate": can_activate,
                "reasons": reasons,
            },
        )

        return OnboardingValidationStatus(
            communication_connected=email_connected,
            has_booking_types=has_booking_types,
            has_availability=has_availability,
            can_activate=can_activate,
            reasons=reasons,
        )

    def _log_event(
        self,
        workspace: Workspace,
        event_type: str,
        actor_type: ActorType,
        payload: dict | None = None,
        actor_id: str | None = None,
    ) -> None:
        ev = EventLog(
            workspace_id=workspace.id,
            event_type=event_type,
            entity_type="workspace",
            entity_id=str(workspace.id),
            actor_type=actor_type,
            actor_id=actor_id,
            payload=payload or {},
        )
        self.db.add(ev)
from datetime import date, datetime, time, timedelta
from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.availability import AvailabilityRule, BlockedSlot # You'll create these models
from app.schemas.owner_availability import (
    AvailabilityRuleCreate,
    AvailabilityRuleUpdate,
    BlockedSlotCreate,
    AvailabilityRuleOut,
    BlockedSlotOut,
    OwnerAvailabilitySlotOut,
)

class OwnerAvailabilityService:
    def __init__(self, db: Session):
        self.db = db

    def create_availability_rule(self, workspace_id: UUID, rule_data: AvailabilityRuleCreate) -> AvailabilityRule:
        db_rule = AvailabilityRule(**rule_data.model_dump(), workspace_id=workspace_id)
        self.db.add(db_rule)
        self.db.commit()
        self.db.refresh(db_rule)
        return db_rule

    def list_availability_rules(self, workspace_id: UUID) -> List[AvailabilityRule]:
        return self.db.query(AvailabilityRule).filter(AvailabilityRule.workspace_id == workspace_id).all()

    def update_availability_rule(self, workspace_id: UUID, rule_id: UUID, rule_update: AvailabilityRuleUpdate) -> Optional[AvailabilityRule]:
        db_rule = self.db.query(AvailabilityRule).filter(
            AvailabilityRule.id == rule_id,
            AvailabilityRule.workspace_id == workspace_id
        ).first()
        if db_rule:
            for key, value in rule_update.model_dump(exclude_unset=True).items():
                setattr(db_rule, key, value)
            self.db.commit()
            self.db.refresh(db_rule)
        return db_rule

    def delete_availability_rule(self, workspace_id: UUID, rule_id: UUID) -> bool:
        db_rule = self.db.query(AvailabilityRule).filter(
            AvailabilityRule.id == rule_id,
            AvailabilityRule.workspace_id == workspace_id
        ).first()
        if db_rule:
            self.db.delete(db_rule)
            self.db.commit()
            return True
        return False

    def create_blocked_slot(self, workspace_id: UUID, slot_data: BlockedSlotCreate) -> BlockedSlot:
        db_slot = BlockedSlot(**slot_data.model_dump(), workspace_id=workspace_id)
        self.db.add(db_slot)
        self.db.commit()
        self.db.refresh(db_slot)
        return db_slot

    def list_blocked_slots(self, workspace_id: UUID, from_date: date, to_date: date) -> List[BlockedSlot]:
        return self.db.query(BlockedSlot).filter(
            BlockedSlot.workspace_id == workspace_id,
            BlockedSlot.start_datetime <= datetime.combine(to_date, time.max),
            BlockedSlot.end_datetime >= datetime.combine(from_date, time.min),
        ).all()

    def delete_blocked_slot(self, workspace_id: UUID, slot_id: UUID) -> bool:
        db_slot = self.db.query(BlockedSlot).filter(
            BlockedSlot.id == slot_id,
            BlockedSlot.workspace_id == workspace_id
        ).first()
        if db_slot:
            self.db.delete(db_slot)
            self.db.commit()
            return True
        return False

    def get_owner_availability_calendar(
        self, workspace_id: UUID, from_date: date, to_date: date
    ) -> List[OwnerAvailabilitySlotOut]:
        """
        Generates a consolidated view of owner availability for a date range.
        This is a simplified example; real-world logic might be more complex.
        """
        rules = self.list_availability_rules(workspace_id)
        blocked_slots = self.list_blocked_slots(workspace_id, from_date, to_date)

        owner_calendar_slots: List[OwnerAvailabilitySlotOut] = []
        current_date = from_date
        while current_date <= to_date:
            day_of_week = current_date.weekday() # Monday is 0, Sunday is 6

            # Apply recurring rules
            for rule in rules:
                if rule.is_active and rule.day_of_week == day_of_week:
                    start_dt = datetime.combine(current_date, rule.start_time)
                    end_dt = datetime.combine(current_date, rule.end_time)
                    owner_calendar_slots.append(
                        OwnerAvailabilitySlotOut(
                            start_datetime=start_dt,
                            end_datetime=end_dt,
                            is_available=True,
                            source="rule",
                        )
                    )

            current_date += timedelta(days=1)

        # Apply blocked slots (mark as unavailable)
        for blocked in blocked_slots:
            # Find overlapping available slots and mark them as unavailable or split them
            # This is a simplified approach; a more robust solution would involve
            # interval tree or similar data structures for efficient overlap detection and merging.
            owner_calendar_slots.append(
                OwnerAvailabilitySlotOut(
                    start_datetime=blocked.start_datetime,
                    end_datetime=blocked.end_datetime,
                    is_available=False,
                    source="blocked",
                    reason=blocked.reason,
                )
            )

        # Sort and merge/resolve overlaps for a clean calendar view
        # This part is crucial for a correct calendar display.
        # For simplicity, we're just returning raw slots, but in a real app,
        # you'd process these to show continuous blocks of availability/unavailability.
        owner_calendar_slots.sort(key=lambda x: x.start_datetime)

        return owner_calendar_slots
# app/schemas/workspace.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.models.workspace import WorkspaceStatus
from app.models.users import StaffRole
from app.models.workspace_email_config import EmailProvider


# ---------- Input DTOs ----------

class OwnerUserCreate(BaseModel):
    email: EmailStr = Field(..., description="Owner email address")
    full_name: str = Field(..., max_length=255, description="Owner full name")
    password: str = Field(..., min_length=8, description="Owner password (minimum 8 characters)")


class EmailProviderConfigCreate(BaseModel):
    provider: EmailProvider = EmailProvider.resend
    from_email: EmailStr = Field(..., description="Sender email address for notifications")
    from_name: Optional[str] = None
    api_key_alias: str = Field(..., max_length=255, description="Email provider API key alias")


class BookingTypeCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    duration_minutes: int = Field(..., gt=0)


class AvailabilitySlotCreate(BaseModel):
    booking_type_slug: str
    staff_email: Optional[EmailStr] = None  # if None, generic availability
    start_at: datetime
    end_at: datetime


class WorkspaceOnboardingRequest(BaseModel):
    workspace_name: str = Field(..., max_length=255)
    owner: OwnerUserCreate
    email_provider: EmailProviderConfigCreate
    booking_types: List[BookingTypeCreate]
    availability: List[AvailabilitySlotCreate]


# ---------- Output DTOs ----------

class WorkspaceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: WorkspaceStatus
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "owner_id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        if v is None:
            return None
        if isinstance(v, UUID):
            return str(v)
        return v


class OnboardingValidationStatus(BaseModel):
    communication_connected: bool
    has_booking_types: bool
    has_availability: bool
    can_activate: bool
    reasons: List[str]


class WorkspaceOnboardingResponse(BaseModel):
    workspace: WorkspaceSummary
    owner_id: str
    validation: OnboardingValidationStatus


# ---------- Email config (Settings) ----------

class WorkspaceEmailConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: EmailProvider
    from_email: str
    from_name: Optional[str]
    api_key_alias: str
    is_active: bool


class WorkspaceEmailConfigUpdate(BaseModel):
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    api_key_alias: Optional[str] = Field(default=None, max_length=255)


# ---------- Availability slots (Owner management) ----------

class AvailabilitySlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_type_slug: str
    booking_type_name: str
    start_at: datetime
    end_at: datetime
    staff_name: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def id_to_str(cls, v):
        return str(v) if v else v


class AvailabilitySlotCreateRequest(BaseModel):
    booking_type_slug: str
    start_at: datetime
    end_at: datetime
    staff_email: Optional[EmailStr] = None
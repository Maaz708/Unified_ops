# app/schemas/booking.py
from datetime import datetime, date, timezone
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.models.booking import BookingStatus
from app.models.message import MessageChannel
from app.models.booking_type import BookingType


# ---------- Helpers ----------

def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_datetime(v: datetime | str) -> datetime:
    if isinstance(v, str):
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
    else:
        dt = v
    return _ensure_utc(dt)


# ---------- Input DTOs ----------

class PublicBookingCreateRequest(BaseModel):
    booking_type_slug: str
    # Exact slot start/end (as returned from availability API)
    start_at: datetime
    end_at: datetime
    full_name: str = Field(..., max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def ensure_utc(cls, v: datetime | str) -> datetime:
        return _parse_datetime(v)

    @field_validator("email", "phone", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        if v is not None and isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("phone")
    @classmethod
    def at_least_one_contact(cls, v, info):
        if info.data and "email" in info.data:
            email = info.data["email"]
        else:
            email = None
        if not email and not v:
            raise ValueError("Either email or phone must be provided.")
        return v


class PublicAvailabilityQuery(BaseModel):
    # Day in the workspace's calendar; interpreted as UTC day for now
    date: date


# ---------- Output DTOs ----------

class PublicBookingTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: Optional[str]
    duration_minutes: int

    @field_validator("id", mode="before")
    @classmethod
    def id_to_str(cls, v):
        if v is None:
            return v
        return str(v)


class PublicAvailabilitySlotOut(BaseModel):
    slot_start: datetime
    slot_end: datetime
    staff_name: Optional[str]
    is_available: bool


class PublicBookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: BookingStatus
    start_at: datetime
    end_at: datetime
    contact_id: str
    conversation_id: Optional[str]
    booking_type_id: str

    @field_validator("id", "contact_id", "conversation_id", "booking_type_id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        if v is None:
            return v
        return str(v)


class PublicBookingResponse(BaseModel):
    booking: PublicBookingOut
    message_channel: Optional[MessageChannel] = None
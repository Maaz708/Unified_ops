# app/schemas/staff.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.users import StaffRole

class StaffBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: StaffRole = StaffRole.staff
    is_active: bool = True

class StaffCreate(StaffBase):
    """Schema for creating a new staff user."""
    pass

class StaffUpdate(BaseModel):
    """Schema for updating a staff user."""
    full_name: Optional[str] = None
    role: Optional[StaffRole] = None
    is_active: Optional[bool] = None

class StaffOut(BaseModel):
    """Schema for staff user output."""
    id: str
    email: str
    full_name: Optional[str]
    role: StaffRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

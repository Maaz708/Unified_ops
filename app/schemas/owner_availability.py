from datetime import date, time, datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field

class AvailabilityRuleBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    start_time: time
    end_time: time
    is_active: bool = True

class AvailabilityRuleCreate(AvailabilityRuleBase):
    pass

class AvailabilityRuleUpdate(AvailabilityRuleBase):
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: Optional[bool] = None

class AvailabilityRuleOut(AvailabilityRuleBase):
    id: UUID
    workspace_id: UUID

    class Config:
        from_attributes = True

class BlockedSlotBase(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = None

class BlockedSlotCreate(BlockedSlotBase):
    pass

class BlockedSlotOut(BlockedSlotBase):
    id: UUID
    workspace_id: UUID

    class Config:
        from_attributes = True

class OwnerAvailabilitySlotOut(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    is_available: bool
    source: str # e.g., "rule", "blocked"
    reason: Optional[str] = None # For blocked slots

    class Config:
        from_attributes = True
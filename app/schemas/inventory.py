# app/schemas/inventory.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class InventoryBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    current_quantity: int = Field(..., ge=0)
    reorder_threshold: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=50)

class InventoryCreate(InventoryBase):
    """Schema for creating a new inventory item."""
    pass

class InventoryUpdate(BaseModel):
    """Schema for updating an inventory item."""
    sku: Optional[str] = Field(None, min_length=1, max_length=255)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    current_quantity: Optional[int] = Field(None, ge=0)
    reorder_threshold: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=50)

class InventoryOut(BaseModel):
    """Schema for inventory item output."""
    id: str
    sku: str
    name: str
    description: Optional[str]
    current_quantity: int
    reorder_threshold: Optional[int]
    unit: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InventoryLowStockItem(BaseModel):
    """Schema for low stock inventory items in dashboard."""
    id: str
    sku: str
    name: str
    current_quantity: int
    reorder_threshold: int
    unit: Optional[str]

    class Config:
        from_attributes = True

# app/api/routers/inventory.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies.db import get_db
from app.api.dependencies.auth import get_current_user
from app.models.inventory_item import InventoryItem
from app.models.users import StaffUser, StaffRole
from app.models.workspace import Workspace
from app.schemas.inventory import InventoryCreate, InventoryOut, InventoryUpdate

router = APIRouter(prefix="/inventory", tags=["inventory"])

def _get_workspace_or_403(db: Session, workspace_id: str, current_user: dict, require_owner: bool = False) -> Workspace:
    """Get workspace and verify user access."""
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    
    # Check if user has access to this workspace
    staff_user = db.query(StaffUser).filter(
        StaffUser.workspace_id == workspace_id,
        StaffUser.email == current_user.get("email"),
        StaffUser.is_deleted.is_(False)
    ).first()
    
    if not staff_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Check if owner role is required
    if require_owner and staff_user.role != StaffRole.owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can perform this action")
    
    return workspace

@router.get("/{workspace_id}", response_model=List[InventoryOut])
def list_inventory(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all inventory items for the workspace."""
    workspace = _get_workspace_or_403(db, workspace_id, current_user)
    
    items = db.query(InventoryItem).filter(
        InventoryItem.workspace_id == workspace_id,
        InventoryItem.is_deleted.is_(False)
    ).order_by(InventoryItem.name).all()
    
    return [
        InventoryOut(
            id=str(item.id),
            sku=item.sku,
            name=item.name,
            description=item.description,
            current_quantity=item.current_quantity,
            reorder_threshold=item.reorder_threshold,
            unit=item.unit,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]

@router.post("/{workspace_id}", response_model=InventoryOut)
def create_inventory_item(
    workspace_id: str,
    payload: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new inventory item (owner only)."""
    workspace = _get_workspace_or_403(db, workspace_id, current_user, require_owner=True)
    
    # Check if SKU already exists
    existing = db.query(InventoryItem).filter(
        InventoryItem.workspace_id == workspace_id,
        InventoryItem.sku == payload.sku,
        InventoryItem.is_deleted.is_(False)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item with this SKU already exists")
    
    inventory_item = InventoryItem(
        workspace_id=workspace_id,
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        current_quantity=payload.current_quantity,
        reorder_threshold=payload.reorder_threshold,
        unit=payload.unit,
    )
    
    db.add(inventory_item)
    db.commit()
    db.refresh(inventory_item)
    
    return InventoryOut(
        id=str(inventory_item.id),
        sku=inventory_item.sku,
        name=inventory_item.name,
        description=inventory_item.description,
        current_quantity=inventory_item.current_quantity,
        reorder_threshold=inventory_item.reorder_threshold,
        unit=inventory_item.unit,
        created_at=inventory_item.created_at,
        updated_at=inventory_item.updated_at,
    )

@router.put("/{workspace_id}/{item_id}", response_model=InventoryOut)
def update_inventory_item(
    workspace_id: str,
    item_id: str,
    payload: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update an inventory item (owner only)."""
    workspace = _get_workspace_or_403(db, workspace_id, current_user, require_owner=True)
    
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.workspace_id == workspace_id,
        InventoryItem.is_deleted.is_(False)
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
    
    # Check if new SKU conflicts with existing item
    if payload.sku and payload.sku != item.sku:
        existing = db.query(InventoryItem).filter(
            InventoryItem.workspace_id == workspace_id,
            InventoryItem.sku == payload.sku,
            InventoryItem.id != item_id,
            InventoryItem.is_deleted.is_(False)
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item with this SKU already exists")
    
    # Update fields
    if payload.sku is not None:
        item.sku = payload.sku
    if payload.name is not None:
        item.name = payload.name
    if payload.description is not None:
        item.description = payload.description
    if payload.current_quantity is not None:
        item.current_quantity = payload.current_quantity
    if payload.reorder_threshold is not None:
        item.reorder_threshold = payload.reorder_threshold
    if payload.unit is not None:
        item.unit = payload.unit
    
    db.commit()
    db.refresh(item)
    
    return InventoryOut(
        id=str(item.id),
        sku=item.sku,
        name=item.name,
        description=item.description,
        current_quantity=item.current_quantity,
        reorder_threshold=item.reorder_threshold,
        unit=item.unit,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )

@router.delete("/{workspace_id}/{item_id}")
def delete_inventory_item(
    workspace_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete an inventory item (owner only)."""
    workspace = _get_workspace_or_403(db, workspace_id, current_user, require_owner=True)
    
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.workspace_id == workspace_id,
        InventoryItem.is_deleted.is_(False)
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
    
    item.is_deleted = True
    db.commit()
    
    return {"message": "Inventory item deleted successfully"}

@router.post("/{workspace_id}/{item_id}/adjust")
def adjust_inventory_quantity(
    workspace_id: str,
    item_id: str,
    quantity_change: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Adjust inventory quantity (owner only)."""
    workspace = _get_workspace_or_403(db, workspace_id, current_user, require_owner=True)
    
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.workspace_id == workspace_id,
        InventoryItem.is_deleted.is_(False)
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
    
    new_quantity = item.current_quantity + quantity_change
    if new_quantity < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reduce quantity below 0")
    
    item.current_quantity = new_quantity
    db.commit()
    
    return {
        "message": "Quantity adjusted successfully",
        "old_quantity": item.current_quantity - quantity_change,
        "new_quantity": new_quantity,
        "change": quantity_change
    }

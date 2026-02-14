# app/api/routers/staff.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies.db import get_db
from app.api.dependencies.auth import get_current_user
from app.models.users import StaffUser, StaffRole
from app.models.workspace import Workspace
from app.schemas.staff import StaffCreate, StaffOut, StaffUpdate

router = APIRouter(prefix="/staff", tags=["staff"])

def _get_workspace_or_403(db: Session, workspace_id: str, current_user: dict) -> Workspace:
    """Get workspace and verify user is owner."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    
    # Check if user is owner of this workspace
    staff_user = db.query(StaffUser).filter(
        StaffUser.workspace_id == workspace_id,
        StaffUser.email == current_user.get("email"),
        StaffUser.is_deleted.is_(False)
    ).first()
    
    if not staff_user or staff_user.role != StaffRole.owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can manage staff")
    
    return workspace

@router.get("/{workspace_id}", response_model=List[StaffOut])
def list_staff(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all staff users for the workspace (owner only)."""
    workspace = _get_workspace_or_403(db, workspace_id, current_user)
    
    staff_users = db.query(StaffUser).filter(
        StaffUser.workspace_id == workspace_id,
        StaffUser.is_deleted.is_(False)
    ).all()
    
    return [
        StaffOut(
            id=str(staff.id),
            email=staff.email,
            full_name=staff.full_name,
            role=staff.role,
            is_active=staff.is_active,
            created_at=staff.created_at,
        )
        for staff in staff_users
    ]

@router.post("/{workspace_id}")
def create_staff(
    workspace_id: str,
    payload: StaffCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Invite a new staff user (owner only)."""
    workspace = _get_workspace_or_403(db, workspace_id, current_user)
    
    # Check if staff already exists
    existing = db.query(StaffUser).filter(
        StaffUser.workspace_id == workspace_id,
        StaffUser.email == payload.email,
        StaffUser.is_deleted.is_(False)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Staff user already exists")
    
    # Create staff user with temporary password
    import secrets
    from app.core.security import hash_password
    temp_password = secrets.token_urlsafe(12)
    hashed_password = hash_password(temp_password)
    
    staff_user = StaffUser(
        workspace_id=workspace_id,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hashed_password,
        role=payload.role,
        is_active=True,
    )
    
    db.add(staff_user)
    db.commit()
    db.refresh(staff_user)
    
    # TODO: Send invitation email with temp password
    
    return {
        "id": str(staff_user.id),
        "email": staff_user.email,
        "full_name": staff_user.full_name,
        "role": staff_user.role,
        "is_active": staff_user.is_active,
        "created_at": staff_user.created_at,
        "temp_password": temp_password  # Include temporary password for owner to share
    }

@router.put("/{workspace_id}/{staff_id}", response_model=StaffOut)
def update_staff(
    workspace_id: str,
    staff_id: str,
    payload: StaffUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update staff user (owner only)."""
    workspace = _get_workspace_or_403(db, workspace_id, current_user)
    
    staff_user = db.query(StaffUser).filter(
        StaffUser.id == staff_id,
        StaffUser.workspace_id == workspace_id,
        StaffUser.is_deleted.is_(False)
    ).first()
    if not staff_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user not found")
    
    # Don't allow changing owner role of the only owner
    if staff_user.role == StaffRole.owner and payload.role != StaffRole.owner:
        other_owners = db.query(StaffUser).filter(
            StaffUser.workspace_id == workspace_id,
            StaffUser.role == StaffRole.owner,
            StaffUser.id != staff_id,
            StaffUser.is_deleted.is_(False)
        ).count()
        if other_owners == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove owner role from the only owner")
    
    # Update fields
    if payload.full_name is not None:
        staff_user.full_name = payload.full_name
    if payload.role is not None:
        staff_user.role = payload.role
    if payload.is_active is not None:
        staff_user.is_active = payload.is_active
    
    db.commit()
    db.refresh(staff_user)
    
    return StaffOut(
        id=str(staff_user.id),
        email=staff_user.email,
        full_name=staff_user.full_name,
        role=staff_user.role,
        is_active=staff_user.is_active,
        created_at=staff_user.created_at,
    )

@router.delete("/{workspace_id}/{staff_id}")
def delete_staff(
    workspace_id: str,
    staff_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete staff user (owner only)."""
    workspace = _get_workspace_or_403(db, workspace_id, current_user)
    
    staff_user = db.query(StaffUser).filter(
        StaffUser.id == staff_id,
        StaffUser.workspace_id == workspace_id,
        StaffUser.is_deleted.is_(False)
    ).first()
    if not staff_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user not found")
    
    # Don't allow deleting the last owner
    if staff_user.role == StaffRole.owner:
        other_owners = db.query(StaffUser).filter(
            StaffUser.workspace_id == workspace_id,
            StaffUser.role == StaffRole.owner,
            StaffUser.id != staff_id,
            StaffUser.is_deleted.is_(False)
        ).count()
        if other_owners == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete the only owner")
    
    staff_user.is_deleted = True
    db.commit()
    
    return {"message": "Staff user deleted successfully"}

@router.post("/reset-password")
def reset_password(
    email: str,
    db: Session = Depends(get_db),
):
    """Reset password for staff user (generates new temporary password)."""
    staff_user = db.query(StaffUser).filter(
        StaffUser.email == email,
        StaffUser.is_deleted.is_(False)
    ).first()
    
    if not staff_user:
        # Don't reveal if email exists for security
        return {"message": "If the email exists, a new temporary password has been generated."}
    
    # Generate new temporary password
    import secrets
    from app.core.security import hash_password
    temp_password = secrets.token_urlsafe(12)
    staff_user.hashed_password = hash_password(temp_password)
    
    db.commit()
    
    # TODO: Send email with new temporary password
    
    return {
        "message": "A new temporary password has been generated.",
        "temp_password": temp_password  # In development, show password directly
    }

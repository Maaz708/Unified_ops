# app/api/routers/bookings.py – owner/staff booking actions (auth required)
from uuid import UUID
import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.core.config import settings
from app.models.workspace import Workspace
from app.models.booking import Booking, BookingStatus

router = APIRouter()


def _get_workspace_or_403(db: Session, workspace_id: UUID, current_user: dict) -> Workspace:
    if str(current_user["workspace_id"]) != str(workspace_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workspace")
    ws = db.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


class BookingStatusUpdate(BaseModel):
    status: str  # "confirmed" | "completed" | "no_show" | "cancelled"


@router.patch("/{workspace_id}/bookings/{booking_id}/status")
def update_booking_status(
    workspace_id: UUID,
    booking_id: UUID,
    payload: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Owner or staff: set booking status (e.g. confirm an upcoming booking or mark completed/no_show)."""
    _get_workspace_or_403(db, workspace_id, current_user)
    try:
        new_status = BookingStatus(payload.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status; use confirmed, completed, no_show, or cancelled",
        )
    booking = db.scalar(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.workspace_id == workspace_id,
        )
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    booking.status = new_status
    db.commit()
    return {"id": str(booking.id), "status": booking.status.value}


class EmailConfirmationRequest(BaseModel):
    booking_id: str
    contact_name: str
    email: str
    start_at: str


@router.post("/send-confirmation")
async def send_booking_confirmation(
    request: EmailConfirmationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Send booking confirmation email using Resend API"""
    if not settings.resend_api_key:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    try:
        start_time = request.start_at.replace('Z', '+00:00')  # Ensure proper datetime format
        text = f"Hello {request.contact_name},\n\nYour booking (ID: {request.booking_id}) is confirmed for {start_time}.\n\nThank you!"
        
        email_data = {
            "from": "onboarding@resend.dev",
            "to": [request.email],
            "subject": "Booking Confirmation",
            "text": text
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json"
                },
                json=email_data
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to send email: {response.text}"
                )
                
        return {"message": "Confirmation sent successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")

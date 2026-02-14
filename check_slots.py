#!/usr/bin/env python3

from app.core.database import SessionLocal
from app.models.availability_slot import AvailabilitySlot
from app.models.booking_type import BookingType
from app.models.workspace import Workspace
from uuid import UUID

db = SessionLocal()
try:
    # Get workspace
    ws = db.query(Workspace).filter(Workspace.id == UUID('95f1c665-cd3a-4f52-b521-00f8c7e6182a')).first()
    if ws:
        print(f'Workspace: {ws.name} (ID: {ws.id})')
        
        # Get booking types
        bts = db.query(BookingType).filter(BookingType.workspace_id == ws.id, BookingType.is_deleted.is_(False)).all()
        print(f'Booking types: {len(bts)}')
        for bt in bts:
            print(f'  - {bt.name} (slug: {bt.slug})')
            
            # Get availability slots for this booking type
            slots = db.query(AvailabilitySlot).filter(AvailabilitySlot.booking_type_id == bt.id).all()
            print(f'    Availability slots: {len(slots)}')
            for slot in slots:
                print(f'      - {slot.start_at} to {slot.end_at}')
    else:
        print('Workspace not found')
finally:
    db.close()

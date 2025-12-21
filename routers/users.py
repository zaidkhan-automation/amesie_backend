from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user

router = APIRouter()

@router.get("/profile", response_model=schemas.User)
def get_user_profile(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=schemas.User)
def update_user_profile(
    user_update: schemas.UserCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(models.User).filter(models.User.id == current_user.id).update({
        "full_name": user_update.full_name,
        "phone_number": user_update.phone_number
    })
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/addresses", response_model=List[schemas.Address])
def get_user_addresses(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    addresses = db.query(models.Address).filter(
        models.Address.user_id == current_user.id
    ).all()
    return addresses

@router.post("/addresses", response_model=schemas.Address)
def create_address(
    address: schemas.AddressCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # If this is set as default, unset other default addresses
    if address.is_default:
        db.query(models.Address).filter(
            models.Address.user_id == current_user.id,
            models.Address.is_default == True
        ).update({"is_default": False})
    
    db_address = models.Address(
        user_id=current_user.id,
        **address.dict()
    )
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

@router.put("/addresses/{address_id}", response_model=schemas.Address)
def update_address(
    address_id: int,
    address_update: schemas.AddressCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(models.Address).filter(
        models.Address.id == address_id,
        models.Address.user_id == current_user.id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    # If this is set as default, unset other default addresses
    if address_update.is_default:
        db.query(models.Address).filter(
            models.Address.user_id == current_user.id,
            models.Address.is_default == True,
            models.Address.id != address_id
        ).update({"is_default": False})
    
    for key, value in address_update.dict().items():
        setattr(address, key, value)
    
    db.commit()
    db.refresh(address)
    return address

@router.delete("/addresses/{address_id}")
def delete_address(
    address_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(models.Address).filter(
        models.Address.id == address_id,
        models.Address.user_id == current_user.id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully"}

@router.get("/notifications", response_model=List[schemas.Notification])
def get_user_notifications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notifications for the current user"""
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).order_by(models.Notification.created_at.desc()).all()
    
    return notifications

@router.put("/notifications/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).update({"is_read": True})
    db.commit()
    
    return {"message": "Notification marked as read"}

@router.put("/notifications/mark-all-read")
def mark_all_notifications_as_read(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for the current user"""
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"message": "All notifications marked as read"}

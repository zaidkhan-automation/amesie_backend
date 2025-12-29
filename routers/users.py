from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user

router = APIRouter()

# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────
@router.get("/profile", response_model=schemas.User)
def get_user_profile(
    current_user: models.User = Depends(get_current_user),
):
    return current_user


@router.put("/profile", response_model=schemas.User)
def update_user_profile(
    user_update: schemas.UserCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.User).filter(
        models.User.id == current_user.id
    ).update({
        "full_name": user_update.full_name,
        "phone_number": user_update.phone_number,
    })

    db.commit()
    db.refresh(current_user)
    return current_user


# ─────────────────────────────────────────────
# BUYER LOCATION (POSTGIS)
# ─────────────────────────────────────────────
@router.post("/me/location")
def update_my_location(
    lat: float,
    lng: float,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.execute(
        text("""
            UPDATE users
            SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
            WHERE id = :uid
        """),
        {
            "lng": lng,
            "lat": lat,
            "uid": current_user.id,
        },
    )

    db.commit()
    return {"ok": True}


# ─────────────────────────────────────────────
# ADDRESSES
# ─────────────────────────────────────────────
@router.get("/addresses", response_model=List[schemas.Address])
def get_user_addresses(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(models.Address).filter(
        models.Address.user_id == current_user.id
    ).all()


@router.post("/addresses", response_model=schemas.Address)
def create_address(
    address: schemas.AddressCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if address.is_default:
        db.query(models.Address).filter(
            models.Address.user_id == current_user.id,
            models.Address.is_default.is_(True),
        ).update({"is_default": False})

    db_address = models.Address(
        user_id=current_user.id,
        **address.dict(),
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
    db: Session = Depends(get_db),
):
    address = db.query(models.Address).filter(
        models.Address.id == address_id,
        models.Address.user_id == current_user.id,
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    if address_update.is_default:
        db.query(models.Address).filter(
            models.Address.user_id == current_user.id,
            models.Address.is_default.is_(True),
            models.Address.id != address_id,
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
    db: Session = Depends(get_db),
):
    address = db.query(models.Address).filter(
        models.Address.id == address_id,
        models.Address.user_id == current_user.id,
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully"}


# ─────────────────────────────────────────────
# NOTIFICATIONS (STEP-3 COMPLETE)
# ─────────────────────────────────────────────

# ✅ UNREAD COUNT
@router.get("/notifications/unread-count")
def get_unread_notification_count(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read.is_(False),
    ).count()

    return {"unread_count": count}


# ✅ LIST + PAGINATION + FILTER
@router.get("/notifications", response_model=List[schemas.Notification])
def get_user_notifications(
    skip: int = 0,
    limit: int = 20,
    notification_type: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    )

    if notification_type:
        query = query.filter(
            models.Notification.notification_type == notification_type
        )

    return (
        query
        .order_by(models.Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ✅ MARK SINGLE READ
@router.put("/notifications/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id,
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}


# ✅ MARK ALL READ
@router.put("/notifications/mark-all-read")
def mark_all_notifications_as_read(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read.is_(False),
    ).update({"is_read": True})

    db.commit()
    return {"message": "All notifications marked as read"}

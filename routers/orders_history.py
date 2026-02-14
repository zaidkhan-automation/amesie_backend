# routers/orders_history.py
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user

router = APIRouter()

def is_admin(user: models.User):
    return user and getattr(user, "role", None) == models.UserRole.ADMIN

@router.get("/user/{user_id}", response_model=List[schemas.Order], tags=["orders"])
def get_orders_for_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return order history for a given user_id.
    Allowed if:
      - current_user.id == user_id (self)
      - OR current_user.role == ADMIN
    """
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if current_user.id != user_id and not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    orders = (
        db.query(models.Order)
          .filter(models.Order.user_id == user_id)
          .order_by(models.Order.created_at.desc())
          .all()
    )
    return orders

@router.get("/recent", response_model=List[schemas.Order], tags=["orders"])
def get_recent_orders(
    limit: Optional[int] = 10,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Admin-only: return most recent orders (limit).
    """
    if current_user is None or not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    orders = (
        db.query(models.Order)
          .order_by(models.Order.created_at.desc())
          .limit(limit)
          .all()
    )
    return orders

@router.get("/{order_id}", response_model=schemas.Order, tags=["orders"])
def get_order_by_id(
    order_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return a single order. Allowed if:
      - owner (order.user_id == current_user.id)
      - OR admin
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # If order has no user (guest), allow only admin to view it
    if order.user_id is None:
        if current_user is None or not is_admin(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return order

    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if current_user.id != order.user_id and not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return order

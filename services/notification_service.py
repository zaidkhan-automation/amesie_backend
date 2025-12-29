from sqlalchemy.orm import Session
from db import models
from datetime import datetime


# ─────────────────────────────────────────────
# CORE NOTIFICATION CREATOR
# ─────────────────────────────────────────────
def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    order_id: int | None = None,
):
    notification = models.Notification(
        user_id=user_id,
        title=title,
        message=message,
        # ⚠️ MUST MATCH DB ENUM VALUES
        notification_type=notification_type.lower(),
        order_id=order_id,
        is_read=False,
        created_at=datetime.utcnow(),
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


# ─────────────────────────────────────────────
# BUYER EVENTS
# ─────────────────────────────────────────────
def notify_order_created(
    db: Session,
    user_id: int,
    order_id: int,
):
    return create_notification(
        db=db,
        user_id=user_id,
        title="Order placed",
        message=f"Your order #{order_id} has been placed successfully.",
        notification_type="order_placed",
        order_id=order_id,
    )


def notify_payment_success(
    db: Session,
    user_id: int,
    order_id: int,
):
    return create_notification(
        db=db,
        user_id=user_id,
        title="Payment received",
        message=f"Payment received for order #{order_id}.",
        notification_type="payment_received",
        order_id=order_id,
    )


def notify_order_status_update(
    db: Session,
    user_id: int,
    order_id: int,
    new_status: str,
):
    """
    new_status MUST be one of:
    confirmed | shipped | delivered | cancelled
    """
    return create_notification(
        db=db,
        user_id=user_id,
        title="Order update",
        message=f"Your order #{order_id} status changed to {new_status}.",
        notification_type=f"order_{new_status.lower()}",
        order_id=order_id,
    )


# ─────────────────────────────────────────────
# SELLER EVENTS
# ─────────────────────────────────────────────
def notify_seller_new_order(
    db: Session,
    seller_user_id: int,
    order_id: int,
):
    # ⚠️ DB ENUM DOES NOT SUPPORT seller_new_order
    # Reuse order_placed safely
    return create_notification(
        db=db,
        user_id=seller_user_id,
        title="New order received",
        message=f"You have received a new order #{order_id}.",
        notification_type="order_placed",
        order_id=order_id,
    )

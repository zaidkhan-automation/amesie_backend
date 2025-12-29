import os
import razorpay
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user

from services.orders_service import (
    create_order_db,
    add_order_item_db,
    mark_payment_success_db,
)

# 🔔 Notifications
from services.notification_service import (
    notify_order_created,
    notify_payment_success,
    notify_order_status_update,
    notify_seller_new_order,
)
router = APIRouter()

# ─────────────────────────────────────────────
# Razorpay Client (safe defaults)
# ─────────────────────────────────────────────
razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID", "rzp_test_key"),
        os.getenv("RAZORPAY_KEY_SECRET", "rzp_test_secret"),
    )
)

# ─────────────────────────────────────────────
# CREATE ORDER (ATOMIC + NOTIFICATIONS)
# ─────────────────────────────────────────────
@router.post("/create")
def create_order(
    payload: schemas.OrderCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    cart_items = (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == current_user.id)
        .all()
    )

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # 🔒 Server-side price calculation
    total_amount = 0.0
    products_map = {}

    for item in cart_items:
        product = (
            db.query(models.Product)
            .filter(
                models.Product.id == item.product_id,
                models.Product.is_active.is_(True),
                models.Product.is_deleted.is_(False),
            )
            .first()
        )

        if not product:
            raise HTTPException(status_code=400, detail="Invalid product in cart")

        total_amount += product.price * item.quantity
        products_map[item.product_id] = product

    try:
        # ───── DB TRANSACTION START ─────
        order_id = create_order_db(
            db=db,
            user_id=current_user.id,
            location_id=payload.location_id,
            total=total_amount,
        )

        for item in cart_items:
            add_order_item_db(
                db=db,
                order_id=order_id,
                user_id=current_user.id,
                product_id=item.product_id,
                quantity=item.quantity,
            )

        # 🔔 USER notification
        notify_order_created(
            db=db,
            user_id=current_user.id,
            order_id=order_id,
        )

        # 🔔 SELLER notifications (deduped)
        seller_user_ids = set()
        for product in products_map.values():
            seller_user_ids.add(product.seller.user_id)

        for seller_user_id in seller_user_ids:
            notify_seller_new_order(
                db=db,
                seller_user_id=seller_user_id,
                order_id=order_id,
            )

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # ───── Razorpay Order (OUTSIDE DB LOCK) ─────
    try:
        razorpay_order = razorpay_client.order.create(
            {
                "amount": int(total_amount * 100),
                "currency": "INR",
                "payment_capture": 1,
            }
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Razorpay order creation failed",
        )

    # Store Razorpay order_id
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    order.payment_id = razorpay_order["id"]
    db.commit()

    # Clear cart AFTER everything succeeds
    db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).delete()
    db.commit()

    return {
        "order_id": order_id,
        "razorpay_order_id": razorpay_order["id"],
        "amount": total_amount,
        "currency": "INR",
    }

# ─────────────────────────────────────────────
# VERIFY PAYMENT
# ─────────────────────────────────────────────
@router.post("/verify-payment")
def verify_payment(
    payment_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    required = {
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
    }

    if not required.issubset(payment_data):
        raise HTTPException(status_code=400, detail="Invalid payment payload")

    try:
        razorpay_client.utility.verify_payment_signature(payment_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    order = (
        db.query(models.Order)
        .filter(
            models.Order.payment_id == payment_data["razorpay_order_id"],
            models.Order.user_id == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        mark_payment_success_db(
            db=db,
            order_id=order.id,
            payment_id=payment_data["razorpay_payment_id"],
            method="UPI",
        )

        # 🔔 USER notification
        notify_payment_success(
            db=db,
            user_id=current_user.id,
            order_id=order.id,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to mark payment success",
        )

    return {"message": "Payment verified successfully"}

# ─────────────────────────────────────────────
# GET USER ORDERS
# ─────────────────────────────────────────────
@router.get("/", response_model=List[schemas.Order])
def get_user_orders(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Order)
        .filter(models.Order.user_id == current_user.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )

# ─────────────────────────────────────────────
# GET SINGLE ORDER
# ─────────────────────────────────────────────
@router.get("/{order_id}", response_model=schemas.Order)
def get_order(
    order_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(models.Order)
        .filter(
            models.Order.id == order_id,
            models.Order.user_id == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order

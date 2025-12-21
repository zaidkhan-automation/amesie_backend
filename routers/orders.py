import os
import razorpay
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user

# ✅ DB-level services
from services.orders_service import (
    create_order_db,
    add_order_item_db,
    mark_payment_success_db
)

router = APIRouter()

razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID", "rzp_test_key"),
        os.getenv("RAZORPAY_KEY_SECRET", "rzp_test_secret")
    )
)

# ─────────────────────────────────────────────
# CREATE ORDER
# ─────────────────────────────────────────────
@router.post("/create", response_model=dict)
def create_order(
    payload: schemas.OrderCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    cart_items = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_amount = 0.0
    for item in cart_items:
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id,
            models.Product.is_active == True
        ).first()

        if not product:
            raise HTTPException(status_code=400, detail="Invalid product in cart")

        total_amount += product.price * item.quantity

    # 🔥 DB: create order first
    try:
        order_id = create_order_db(
            db=db,
            user_id=current_user.id,
            location_id=payload.location_id,
            total=total_amount
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 🔥 DB: add items
    try:
        for item in cart_items:
            add_order_item_db(
                db=db,
                order_id=order_id,
                user_id=current_user.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add order items")

    # Razorpay order AFTER DB success
    try:
        razorpay_order = razorpay_client.order.create({
            "amount": int(total_amount * 100),
            "currency": "INR",
            "payment_capture": 1
        })
    except Exception:
        raise HTTPException(status_code=500, detail="Razorpay order failed")

    # Clear cart
    db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).delete()
    db.commit()

    return {
        "order_id": order_id,
        "razorpay_order_id": razorpay_order["id"],
        "amount": total_amount,
        "currency": "INR"
    }


# ─────────────────────────────────────────────
# VERIFY PAYMENT
# ─────────────────────────────────────────────
@router.post("/verify-payment")
def verify_payment(
    payment_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    required = {"razorpay_order_id", "razorpay_payment_id", "razorpay_signature"}
    if not required.issubset(payment_data):
        raise HTTPException(status_code=400, detail="Invalid payment payload")

    try:
        razorpay_client.utility.verify_payment_signature(payment_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    order = db.query(models.Order).filter(
        models.Order.payment_id == payment_data["razorpay_order_id"],
        models.Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    mark_payment_success_db(
        db=db,
        order_id=order.id,
        payment_id=payment_data["razorpay_payment_id"],
        method="UPI"
    )

    return {"message": "Payment verified successfully"}


# ─────────────────────────────────────────────
# READ-ONLY ROUTES
# ─────────────────────────────────────────────
@router.get("/", response_model=List[schemas.Order])
def get_user_orders(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    return db.query(models.Order).filter(
        models.Order.user_id == current_user.id
    ).order_by(models.Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=schemas.Order)
def get_order(
    order_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order

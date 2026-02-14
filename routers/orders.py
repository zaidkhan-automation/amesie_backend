import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user
from services.orders_service import create_order_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create", response_model=schemas.Order)
def create_order(
    payload: schemas.OrderCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(401, "Authentication required")

    cart_items = (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == current_user.id)
        .with_for_update()
        .all()
    )

    if not cart_items:
        raise HTTPException(400, "Cart is empty")

    total_amount = 0.0

    try:
        for item in cart_items:
            product = (
                db.query(models.Product)
                .filter(
                    models.Product.id == item.product_id,
                    models.Product.is_active.is_(True),
                    models.Product.is_deleted.is_(False),
                )
                .with_for_update()
                .first()
            )

            if not product:
                raise HTTPException(400, "Product unavailable")

            if item.quantity > product.stock_quantity:
                raise HTTPException(
                    400,
                    f"Insufficient stock for {product.name}",
                )

            total_amount += product.price * item.quantity

        order_id = create_order_db(
            db=db,
            user_id=current_user.id,
            location_id=payload.location_id,
            total=total_amount,
        )

        # Ranking signal: purchased
        for item in cart_items:
            log = (
                db.query(models.SearchLog)
                .filter(models.SearchLog.product_id == item.product_id)
                .order_by(models.SearchLog.id.desc())
                .first()
            )

            if log:
                log.purchased = True

        db.query(models.CartItem).filter(
            models.CartItem.user_id == current_user.id
        ).delete()

        db.commit()

        return (
            db.query(models.Order)
            .filter(models.Order.id == order_id)
            .first()
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Order conflict")

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        logger.exception("Order creation failed")
        raise HTTPException(500, "Order creation failed")

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user

router = APIRouter()


def _sanitize_cart_items(items: List[models.CartItem]):
    for item in items:
        if item.product and item.product.seller:
            if item.product.seller.rating is None:
                item.product.seller.rating = 0.0
    return items


@router.get("/", response_model=List[schemas.CartItem])
def get_cart_items(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_items = (
        db.query(models.CartItem)
        .options(
            joinedload(models.CartItem.product)
            .joinedload(models.Product.seller)
        )
        .filter(models.CartItem.user_id == current_user.id)
        .all()
    )

    return _sanitize_cart_items(cart_items)


@router.post("/items", response_model=schemas.CartItem)
def add_to_cart(
    cart_item: schemas.CartItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if cart_item.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than zero",
        )

    product = (
        db.query(models.Product)
        .with_for_update()
        .filter(
            models.Product.id == cart_item.product_id,
            models.Product.is_active.is_(True),
            models.Product.is_deleted.is_(False),
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.user_id == current_user.id,
            models.CartItem.product_id == cart_item.product_id,
        )
        .first()
    )

    total_quantity = cart_item.quantity
    if existing_item:
        total_quantity += existing_item.quantity

    if total_quantity > product.stock_quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product.stock_quantity} units available",
        )

    if existing_item:
        existing_item.quantity = total_quantity
        db.commit()
        db.refresh(existing_item)
        updated_item = existing_item
    else:
        new_item = models.CartItem(
            user_id=current_user.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        updated_item = new_item

    # Ranking signal: added_to_cart
    log = (
        db.query(models.SearchLog)
        .filter(models.SearchLog.product_id == cart_item.product_id)
        .order_by(models.SearchLog.id.desc())
        .first()
    )

    if log:
        log.added_to_cart = True
        db.commit()

    return _sanitize_cart_items([updated_item])[0]


@router.put("/items/{item_id}")
def update_cart_item(
    item_id: int,
    quantity: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_item = (
        db.query(models.CartItem)
        .options(joinedload(models.CartItem.product))
        .filter(
            models.CartItem.id == item_id,
            models.CartItem.user_id == current_user.id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if quantity <= 0:
        db.delete(cart_item)
        db.commit()
        return {"message": "Cart item removed"}

    product = (
        db.query(models.Product)
        .with_for_update()
        .filter(models.Product.id == cart_item.product_id)
        .first()
    )

    if not product or product.is_deleted or not product.is_active:
        raise HTTPException(400, "Product is no longer available")

    if quantity > product.stock_quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product.stock_quantity} units available",
        )

    cart_item.quantity = quantity
    db.commit()
    return {"message": "Cart item updated successfully"}


@router.delete("/items/{item_id}")
def remove_from_cart(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.id == item_id,
            models.CartItem.user_id == current_user.id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(cart_item)
    db.commit()
    return {"message": "Item removed from cart"}

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user

router = APIRouter()


# ─────────────────────────────────────────────
# INTERNAL SANITIZER (FIXES RESPONSE CRASHES)
# ─────────────────────────────────────────────
def _sanitize_cart_items(items: List[models.CartItem]):
    """
    Fix nullable fields that break Pydantic validation.
    """
    for item in items:
        if item.product and item.product.seller:
            if item.product.seller.rating is None:
                item.product.seller.rating = 0.0
    return items


# ─────────────────────────────────────────────
# GET CART ITEMS
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# ADD TO CART
# ─────────────────────────────────────────────
@router.post("/items", response_model=schemas.CartItem)
def add_to_cart(
    cart_item: schemas.CartItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == cart_item.product_id,
            models.Product.is_active.is_(True),
            models.Product.is_deleted.is_(False),
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    existing_item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.user_id == current_user.id,
            models.CartItem.product_id == cart_item.product_id,
        )
        .first()
    )

    if existing_item:
        existing_item.quantity += cart_item.quantity
        db.commit()
        db.refresh(existing_item)
        return _sanitize_cart_items([existing_item])[0]

    db_cart_item = models.CartItem(
        user_id=current_user.id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
    )

    db.add(db_cart_item)
    db.commit()
    db.refresh(db_cart_item)
    return _sanitize_cart_items([db_cart_item])[0]


# ─────────────────────────────────────────────
# UPDATE CART ITEM
# ─────────────────────────────────────────────
@router.put("/items/{item_id}")
def update_cart_item(
    item_id: int,
    quantity: int,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    if quantity <= 0:
        db.delete(cart_item)
    else:
        cart_item.quantity = quantity

    db.commit()
    return {"message": "Cart item updated successfully"}


# ─────────────────────────────────────────────
# REMOVE ITEM
# ─────────────────────────────────────────────
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    db.delete(cart_item)
    db.commit()
    return {"message": "Item removed from cart"}


# ─────────────────────────────────────────────
# CLEAR CART
# ─────────────────────────────────────────────
@router.delete("/clear")
def clear_cart(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).delete()

    db.commit()
    return {"message": "Cart cleared successfully"}


# ─────────────────────────────────────────────
# WISHLIST
# ─────────────────────────────────────────────
@router.get("/wishlist", response_model=List[schemas.WishlistItem])
def get_wishlist(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(models.WishlistItem)
        .options(
            joinedload(models.WishlistItem.product)
            .joinedload(models.Product.seller)
        )
        .filter(models.WishlistItem.user_id == current_user.id)
        .all()
    )

    # sanitize seller.rating here too
    for item in items:
        if item.product and item.product.seller:
            if item.product.seller.rating is None:
                item.product.seller.rating = 0.0

    return items


@router.post("/wishlist", response_model=schemas.WishlistItem)
def add_to_wishlist(
    wishlist_item: schemas.WishlistItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exists = (
        db.query(models.WishlistItem)
        .filter(
            models.WishlistItem.user_id == current_user.id,
            models.WishlistItem.product_id == wishlist_item.product_id,
        )
        .first()
    )

    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already in wishlist",
        )

    item = models.WishlistItem(
        user_id=current_user.id,
        product_id=wishlist_item.product_id,
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/wishlist/{item_id}")
def remove_from_wishlist(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.WishlistItem)
        .filter(
            models.WishlistItem.id == item_id,
            models.WishlistItem.user_id == current_user.id,
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found",
        )

    db.delete(item)
    db.commit()
    return {"message": "Item removed from wishlist"}

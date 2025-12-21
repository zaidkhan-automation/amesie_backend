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

@router.get("/", response_model=List[schemas.CartItem])
def get_cart_items(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_items = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).all()
    return cart_items

@router.post("/items", response_model=schemas.CartItem)
def add_to_cart(
    cart_item: schemas.CartItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if product exists
    product = db.query(models.Product).filter(
        models.Product.id == cart_item.product_id,
        models.Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if item already in cart
    existing_item = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id,
        models.CartItem.product_id == cart_item.product_id
    ).first()
    
    if existing_item:
        # Update quantity
        new_quantity = existing_item.quantity + cart_item.quantity
        db.query(models.CartItem).filter(models.CartItem.id == existing_item.id).update({"quantity": new_quantity})
        db.commit()
        db.refresh(existing_item)
        return existing_item
    else:
        # Create new cart item
        db_cart_item = models.CartItem(
            user_id=current_user.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity
        )
        db.add(db_cart_item)
        db.commit()
        db.refresh(db_cart_item)
        return db_cart_item

@router.put("/items/{item_id}")
def update_cart_item(
    item_id: int,
    quantity: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    if quantity <= 0:
        db.delete(cart_item)
    else:
        db.query(models.CartItem).filter(models.CartItem.id == item_id).update({"quantity": quantity})
    
    db.commit()
    return {"message": "Cart item updated successfully"}

@router.delete("/items/{item_id}")
def remove_from_cart(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    db.delete(cart_item)
    db.commit()
    return {"message": "Item removed from cart"}

@router.delete("/clear")
def clear_cart(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).delete()
    db.commit()
    return {"message": "Cart cleared successfully"}

# Wishlist endpoints
@router.get("/wishlist", response_model=List[schemas.WishlistItem])
def get_wishlist(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wishlist_items = db.query(models.WishlistItem).filter(
        models.WishlistItem.user_id == current_user.id
    ).all()
    return wishlist_items

@router.post("/wishlist", response_model=schemas.WishlistItem)
def add_to_wishlist(
    wishlist_item: schemas.WishlistItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if already in wishlist
    existing_item = db.query(models.WishlistItem).filter(
        models.WishlistItem.user_id == current_user.id,
        models.WishlistItem.product_id == wishlist_item.product_id
    ).first()
    
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already in wishlist"
        )
    
    db_wishlist_item = models.WishlistItem(
        user_id=current_user.id,
        product_id=wishlist_item.product_id
    )
    db.add(db_wishlist_item)
    db.commit()
    db.refresh(db_wishlist_item)
    return db_wishlist_item

@router.delete("/wishlist/{item_id}")
def remove_from_wishlist(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wishlist_item = db.query(models.WishlistItem).filter(
        models.WishlistItem.id == item_id,
        models.WishlistItem.user_id == current_user.id
    ).first()
    
    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found"
        )
    
    db.delete(wishlist_item)
    db.commit()
    return {"message": "Item removed from wishlist"}

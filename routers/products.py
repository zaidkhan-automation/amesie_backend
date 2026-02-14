# routers/products.py

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, text

from core.database import get_db
from db import models

router = APIRouter()

# ─────────────────────────────────────────────
# LIST PRODUCTS
# ─────────────────────────────────────────────
@router.get("/")
def get_products(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[int] = None,
    include_children: bool = True,
    seller_id: Optional[int] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(models.Product)
        .options(selectinload(models.Product.images))
        .filter(models.Product.is_deleted.is_(False))
    )

    if is_active is not None:
        query = query.filter(models.Product.is_active == is_active)

    if category_id:
        if include_children:
            child_ids = db.execute(
                text("SELECT id FROM product_categories WHERE parent_id = :pid"),
                {"pid": category_id},
            ).fetchall()
            ids = [category_id] + [c.id for c in child_ids]
            query = query.filter(models.Product.category_id.in_(ids))
        else:
            query = query.filter(models.Product.category_id == category_id)

    if seller_id:
        query = query.filter(models.Product.seller_id == seller_id)

    if search:
        query = query.filter(
            or_(
                models.Product.name.ilike(f"%{search}%"),
                models.Product.description.ilike(f"%{search}%"),
                models.Product.sku.ilike(f"%{search}%"),
            )
        )

    products = query.offset(skip).limit(limit).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "sku": p.sku,
            "stock_quantity": p.stock_quantity,
            "category_id": p.category_id,
            "seller_id": p.seller_id,
            "is_active": p.is_active,
            "images": [
                {
                    "id": img.id,
                    "image_url": img.image_url,
                    "is_primary": img.is_primary,
                    "display_order": img.display_order,
                }
                for img in p.images
            ],
        }
        for p in products
    ]


# ─────────────────────────────────────────────
# SINGLE PRODUCT
# ─────────────────────────────────────────────
@router.get("/{product_id:int}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = (
        db.query(models.Product)
        .options(selectinload(models.Product.images))
        .filter(
            models.Product.id == product_id,
            models.Product.is_active.is_(True),
            models.Product.is_deleted.is_(False),
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "sku": product.sku,
        "stock_quantity": product.stock_quantity,
        "category_id": product.category_id,
        "seller_id": product.seller_id,
        "is_active": product.is_active,
        "images": [
            {
                "id": img.id,
                "image_url": img.image_url,
                "is_primary": img.is_primary,
                "display_order": img.display_order,
            }
            for img in product.images
        ],
    }

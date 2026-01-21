# agents/tools/seller_create_product.py
from core.database import SessionLocal

from sqlalchemy.orm import Session
from fastapi import HTTPException
from db import models
from db.models import Product
import re
import uuid

DEFAULT_CATEGORY_ID = 1  # must exist in categories table
def run(name, price, stock_quantity, description=None, image_url=None):
    db = SessionLocal()
    try:
        product = Product(
            name=name,
            description=description or "",
            price=price,
            stock_quantity=stock_quantity,
            sku=f"AUTO-{uuid.uuid4().hex[:8]}",
            image_url=image_url
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock_quantity": product.stock_quantity
        }
    finally:
        db.close()
def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def create_product(
    *,
    seller_id: int,
    name: str,
    description: str | None = None,
    price: float,
    stock: int,
    db: Session,
):
    # 🔒 Category must exist
    category = (
        db.query(models.Category)
        .filter(models.Category.id == DEFAULT_CATEGORY_ID)
        .first()
    )

    if not category:
        raise HTTPException(400, "Category does not exist")

    # 🔑 Collision-proof SKU
    slug = _slugify(name)
    unique_suffix = uuid.uuid4().hex[:6].upper()
    sku = f"AUTO-{seller_id}-{slug}-{unique_suffix}"

    product = models.Product(
        name=name,
        description=description,          # ✅ FIXED (was missing)
        price=price,
        stock_quantity=stock,
        seller_id=seller_id,
        category_id=category.id,
        is_active=True,
        is_deleted=False,
        sku=sku,
    )

    db.add(product)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(400, "Failed to create product")

    db.refresh(product)

    return {
        "product_id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock_quantity,
        "category_id": product.category_id,
        "sku": product.sku,
    }

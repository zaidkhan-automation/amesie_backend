# agents/tools/seller_create_product.py

import uuid
import re
from sqlalchemy.orm import Session
from fastapi import HTTPException
from db import models

DEFAULT_CATEGORY_ID = 1

def _slugify(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")

def create_product(
    *,
    seller_id: int,
    name: str,
    description: str | None,
    price: float,
    stock: int,
    db: Session,
):
    category = (
        db.query(models.Category)
        .filter(models.Category.id == DEFAULT_CATEGORY_ID)
        .first()
    )

    if not category:
        raise HTTPException(400, "Category does not exist")

    slug = _slugify(name)
    sku = f"AUTO-{seller_id}-{slug}-{uuid.uuid4().hex[:6].upper()}"

    product = models.Product(
        seller_id=seller_id,
        name=name,
        description=description or "",
        price=price,
        stock_quantity=stock,
        category_id=category.id,
        sku=sku,
        is_active=True,
        is_deleted=False,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return {
        "product_id": product.id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock_quantity,
        "sku": product.sku,
    }

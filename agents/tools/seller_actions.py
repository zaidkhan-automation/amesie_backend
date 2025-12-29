from sqlalchemy.orm import Session
from db import models
from fastapi import HTTPException


def delete_product(*, seller_id: int, product_id: int, db: Session):
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id,
            models.Product.seller_id == seller_id,
            models.Product.is_deleted.is_(False),
        )
        .first()
    )

    if not product:
        raise HTTPException(404, "Product not found or not owned by seller")

    product.is_deleted = True
    product.is_active = False
    db.commit()

    return {
        "product_id": product_id,
        "status": "deleted",
    }


def update_stock(*, seller_id: int, product_id: int, stock: int, db: Session):
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id,
            models.Product.seller_id == seller_id,
            models.Product.is_deleted.is_(False),
        )
        .first()
    )

    if not product:
        raise HTTPException(404, "Product not found or not owned by seller")

    product.stock_quantity = stock
    db.commit()

    return {
        "product_id": product_id,
        "new_stock": stock,
    }

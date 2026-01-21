# agents/tools/seller_update_stock.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
from db.models import Product

def update_stock(
    *,
    seller_id: int,
    product_id: int,
    stock: int,
    db: Session,
):
    if stock < 0:
        raise HTTPException(400, "Stock cannot be negative")

    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.seller_id == seller_id,
            Product.is_deleted.is_(False),
        )
        .first()
    )

    if not product:
        raise HTTPException(404, "Product not found or not owned by seller")

    product.stock_quantity = stock
    db.commit()
    db.refresh(product)

    return {
        "product_id": product.id,
        "new_stock": product.stock_quantity,
    }

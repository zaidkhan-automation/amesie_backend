from fastapi import HTTPException
from sqlalchemy.orm import Session
from core.database import SessionLocal
from db.models import Product

def update_price(
    seller_id: int,
    product_id: int,
    new_price: float,
    db: Session,
):
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.seller_id == seller_id,
            Product.is_deleted == False,
        )
        .first()
    )

    if not product:
        raise HTTPException(404, "Product not found or not owned by seller")

    product.price = new_price
    db.commit()
    db.refresh(product)

    return {
        "product_id": product.id,
        "new_price": product.price,
    }

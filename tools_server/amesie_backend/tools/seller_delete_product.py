from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models import Product
from datetime import datetime
from core.database import SessionLocal
from db.models import Product
from core.database import SessionLocal
def run(product_id: int):
    db = SessionLocal()
    try:
        product = db.query(Product).get(product_id)
        if not product:
            raise ValueError("Product not found")
        db.delete(product)
        db.commit()
        return {"status": "deleted", "product_id": product_id}
    finally:
        db.close()
def delete_product(
    seller_id: int,
    product_id: int,
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

    product.is_deleted = True
    product.deleted_at = datetime.utcnow()
    db.commit()

    return {
        "product_id": product_id,
        "status": "deleted",
    }

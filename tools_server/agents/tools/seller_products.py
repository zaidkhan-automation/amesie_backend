# agents/tools/seller_products.py
from sqlalchemy.orm import Session
from core.database import get_db
from core.database import SessionLocal
from db.models import Product

from db import models
def run():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "stock": p.stock,
                "is_active": p.is_active
            }
            for p in products
        ]
    finally:
        db.close()
def list_seller_products(seller_id: int, db: Session):
    products = (
        db.query(models.Product)
        .filter(
            models.Product.seller_id == seller_id,
            models.Product.is_deleted.is_(False),
        )
        .all()
    )

    return [
        {
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock_quantity,
            "is_active": p.is_active,
        }
        for p in products
    ]

"""
One-off safe seeder to insert espresso-brown-coffee SKU into products.
Run:
    python -m scripts.seed_coffee
or
    PYTHONPATH=. python scripts/seed_coffee.py
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, engine
from db import models
from sqlalchemy.orm import Session

def seed():
    db: Session = SessionLocal()
    try:
        sku = "espresso-brown-coffee"
        exists = db.query(models.Product).filter(models.Product.sku == sku).first()
        if exists:
            print("SKU already exists:", sku)
            return

        p = models.Product(
            name="Espresso Brown Coffee",
            description="Small espresso brown coffee - 250ml",
            price=5.99,
            sku=sku,
            stock_quantity=100,
            image_url="",
            is_active=True,
        )
        db.add(p)
        db.commit()
        print("Seeded product:", sku)
    except Exception as e:
        db.rollback()
        print("Seeder failed:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed()

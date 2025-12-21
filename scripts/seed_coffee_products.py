# backend/scripts/seed_coffee_products.py
import sys
import os

# backend ko import path me daalne ke liye
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from core.database import SessionLocal, engine
from db import models

COFFEE_PRODUCTS = [
    {
        "name": "Espresso Brown Coffee",
        "description": "Complex flavour, premium espresso blend",
        "price": 5.99,
        "sku": "espresso-brown-coffee",
        "image_url": "/static/images/coffee/espresso-brown.png",
        "stock_quantity": 100,
    },
    {
        "name": "Iced Brown Coffee",
        "description": "Smooth & creamy iced coffee",
        "price": 5.49,
        "sku": "iced-brown-coffee",
        "image_url": "/static/images/coffee/iced-brown.png",
        "stock_quantity": 100,
    },
    {
        "name": "Americano",
        "description": "Smoothly bold",
        "price": 4.99,
        "sku": "americano-coffee",
        "image_url": "/static/images/coffee/americano.png",
        "stock_quantity": 100,
    },
]

def main():
    db = SessionLocal()
    try:
        # ensure tables exist (safety)
        models.Base.metadata.create_all(bind=engine)

        # simple category for coffee
        coffee_cat = (
            db.query(models.Category)
            .filter(models.Category.name == "Coffee")
            .first()
        )
        if not coffee_cat:
            coffee_cat = models.Category(
                name="Coffee",
                description="Premium coffee drinks",
            )
            db.add(coffee_cat)
            db.commit()
            db.refresh(coffee_cat)
            print(f"[SEED] Created category Coffee with id={coffee_cat.id}")

        for item in COFFEE_PRODUCTS:
            existing = (
                db.query(models.Product)
                .filter(models.Product.sku == item["sku"])
                .first()
            )
            if existing:
                print(f"[SEED] SKU {item['sku']} already exists, skipping")
                continue

            product = models.Product(
                name=item["name"],
                description=item["description"],
                price=item["price"],
                sku=item["sku"],
                image_url=item["image_url"],
                stock_quantity=item["stock_quantity"],
                category_id=coffee_cat.id,
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            print(f"[SEED] Inserted product {product.name} with id={product.id}")

    finally:
        db.close()

if __name__ == "__main__":
    main()

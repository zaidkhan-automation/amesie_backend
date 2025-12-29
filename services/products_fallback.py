from sqlalchemy.orm import Session
from sqlalchemy import desc
from db import models


def fallback_recommendations(
    db: Session,
    product_id: int,
    limit: int = 5,
):
    # 1️⃣ Get current product
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id,
            models.Product.is_active == True,
            models.Product.is_deleted == False,
        )
        .first()
    )

    if not product:
        return []

    # 2️⃣ Same category fallback
    same_category = (
        db.query(models.Product)
        .filter(
            models.Product.category_id == product.category_id,
            models.Product.id != product_id,
            models.Product.is_active == True,
            models.Product.is_deleted == False,
        )
        .order_by(
            desc(models.Product.sold_count),
            models.Product.id.asc(),
        )
        .limit(limit)
        .all()
    )

    if same_category:
        return same_category

    # 3️⃣ Global popular fallback
    popular = (
        db.query(models.Product)
        .filter(
            models.Product.is_active == True,
            models.Product.is_deleted == False,
        )
        .order_by(
            desc(models.Product.sold_count),
            models.Product.id.asc(),
        )
        .limit(limit)
        .all()
    )

    return popular

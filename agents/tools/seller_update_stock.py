from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import Product


def update_stock(
    seller_id: int,
    product_id: int,
    stock: int,
    db: Session,
):
    # basic sanity check
    if stock < 0:
        raise HTTPException(status_code=400, detail="Stock cannot be negative")

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
        raise HTTPException(
            status_code=404,
            detail="Product not found or not owned by seller",
        )

    product.stock_quantity = stock
    db.commit()
    db.refresh(product)

    return {
        "product_id": product.id,
        "new_stock": product.stock_quantity,
    }

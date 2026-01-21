# agents/tools/seller_add_product_image.py

from sqlalchemy.orm import Session
from fastapi import HTTPException

from db import models
from services.product_image_service import handle_product_image_upload

MAX_IMAGES_PER_PRODUCT = 5

def run(product_id: int, image_url: str):
    return {
        "product_id": product_id,
        "image_url": image_url,
        "status": "attached"
    }
def add_product_image(
    *,
    seller_id: int,
    product_id: int,
    raw_bytes: bytes,
    db: Session,
):
    """
    Adds a processed WEBP image to a seller's product.
    Ownership MUST be enforced here.
    """

    # 1️⃣ Verify product ownership
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id,
            models.Product.seller_id == seller_id,
            models.Product.is_deleted == False,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found or not owned by seller.",
        )

    # 2️⃣ Count existing images
    existing_images = (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .order_by(models.ProductImage.id.asc())
        .all()
    )

    if len(existing_images) >= MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(
            status_code=400,
            detail="Maximum number of product images reached.",
        )

    position = len(existing_images) + 1
    is_primary = position == 1

    # 3️⃣ Process & store image
    image_path, final_size = handle_product_image_upload(
        seller_id=seller_id,
        product_id=product_id,
        raw_bytes=raw_bytes,
        position=position,
    )

    # 4️⃣ Persist metadata
    image = models.ProductImage(
        product_id=product_id,
        image_url=image_path,
        is_primary=is_primary,
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return {
        "image_id": image.id,
        "product_id": product_id,
        "image_url": image.image_url,
        "is_primary": image.is_primary,
        "size_bytes": final_size,
    }

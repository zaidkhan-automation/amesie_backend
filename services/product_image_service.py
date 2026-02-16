import os
from typing import Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db import models
from utils.image_processor import process_image_to_webp

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_FINAL_WEBP_BYTES = 500 * 1024
BASE_STORAGE_PATH = "storage/products"


def handle_product_image_upload(
    *,
    db: Session,
    seller_id: int,
    product_id: int,
    raw_bytes: bytes,
) -> Tuple[str, int]:

    # Validate product ownership
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
        raise HTTPException(status_code=404, detail="Invalid product or seller")

    # Determine display order
    last_image = (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .order_by(models.ProductImage.display_order.desc())
        .first()
    )

    if last_image:
        display_order = last_image.display_order + 1
        is_primary = False
    else:
        display_order = 1
        is_primary = True

    # Validate size before processing
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large")

    # Convert to optimized webp
    webp_bytes, final_size, mime = process_image_to_webp(raw_bytes)

    if mime != "image/webp":
        raise HTTPException(status_code=400, detail="Invalid image format")

    if final_size > MAX_FINAL_WEBP_BYTES:
        raise HTTPException(status_code=400, detail="Compressed image exceeds limit")

    # Build folder path
    folder_path = os.path.join(
        BASE_STORAGE_PATH,
        f"seller_{seller_id}",
        f"product_{product_id}",
    )
    os.makedirs(folder_path, exist_ok=True)

    filename = f"{display_order}.webp"
    disk_path = os.path.join(folder_path, filename)

    # Atomic write
    tmp_path = disk_path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(webp_bytes)
    os.replace(tmp_path, disk_path)

    public_url = "/" + disk_path.replace("\\", "/")

    # Create DB record (NO commit here)
    image = models.ProductImage(
        product_id=product_id,
        image_url=public_url,
        display_order=display_order,
        is_primary=is_primary,
    )

    db.add(image)

    return public_url, final_size

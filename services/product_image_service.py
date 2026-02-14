import os
from typing import Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models.product_image import ProductImage
from core.database import SessionLocal
from db import models
from utils.image_processor import process_image_to_webp

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_FINAL_WEBP_BYTES = 500 * 1024
BASE_STORAGE_PATH = "storage/products"


def handle_product_image_upload(
    *,
    seller_id: int,
    product_id: int,
    raw_bytes: bytes,
) -> Tuple[str, int]:

    db: Session = SessionLocal()

    try:
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
            raise HTTPException(404, "Invalid product or seller")

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

        if len(raw_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Image too large (max 2MB)")

        webp_bytes, final_size, mime = process_image_to_webp(raw_bytes)

        if mime != "image/webp":
            raise HTTPException(400, "Invalid image format")

        if final_size > MAX_FINAL_WEBP_BYTES:
            raise HTTPException(400, "Compressed image exceeds 500KB")

        folder_path = os.path.join(
            BASE_STORAGE_PATH,
            f"seller_{seller_id}",
            f"product_{product_id}",
        )
        os.makedirs(folder_path, exist_ok=True)

        filename = f"{display_order}.webp"
        disk_path = os.path.join(folder_path, filename)

        tmp_path = disk_path + ".tmp"
        with open(tmp_path, "wb") as f:
            f.write(webp_bytes)
        os.replace(tmp_path, disk_path)

        public_url = "/" + disk_path.replace("\\", "/")

        image = models.ProductImage(
            product_id=product_id,
            image_url=public_url,
            display_order=display_order,
            is_primary=is_primary,
        )

        db.add(image)
        db.commit()

        return public_url, final_size

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Image upload failed: {str(e)}")

    finally:
        db.close()

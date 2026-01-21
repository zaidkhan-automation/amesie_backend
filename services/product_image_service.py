# services/product_image_service.py

import os
from typing import Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.database import SessionLocal
from db import models
from utils.image_processor import process_image_to_webp

# -------------------------
# CONFIG
# -------------------------
MAX_UPLOAD_BYTES = 2 * 1024 * 1024      # 2MB upload limit
MAX_FINAL_WEBP_BYTES = 500 * 1024       # 500KB after compression

BASE_STORAGE_PATH = "storage/products"


# -------------------------
# CORE SERVICE
# -------------------------
def handle_product_image_upload(
    *,
    seller_id: int,
    product_id: int,
    raw_bytes: bytes,
) -> Tuple[str, int]:
    """
    Validates, converts, compresses, stores image,
    AND creates DB record with correct ordering + primary logic.

    Rules:
    - First image → primary = True, order = 1
    - Next images → primary = False, order = max + 1
    """

    db: Session = SessionLocal()

    try:
        # 🔒 Ensure product ownership
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

        # 📊 Existing images
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

        # 1️⃣ Upload size guard
        if len(raw_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Image too large. Max 2MB.")

        # 2️⃣ Convert → WEBP
        try:
            webp_bytes, final_size, mime = process_image_to_webp(raw_bytes)
        except Exception:
            raise HTTPException(400, "Invalid image file.")

        if mime != "image/webp":
            raise HTTPException(400, "Image conversion failed.")

        if final_size > MAX_FINAL_WEBP_BYTES:
            raise HTTPException(400, "Compressed image exceeds 500KB.")

        # 3️⃣ Storage path
        folder_path = os.path.normpath(
            os.path.join(
                BASE_STORAGE_PATH,
                f"seller_{seller_id}",
                f"product_{product_id}",
            )
        )
        os.makedirs(folder_path, exist_ok=True)

        filename = f"{display_order}.webp"
        final_path = os.path.join(folder_path, filename)
        temp_path = final_path + ".tmp"

        # 4️⃣ Atomic write
        with open(temp_path, "wb") as f:
            f.write(webp_bytes)
        os.replace(temp_path, final_path)

        # 5️⃣ DB record
        image = models.ProductImage(
            product_id=product_id,
            image_url=final_path,
            display_order=display_order,
            is_primary=is_primary,
        )

        db.add(image)
        db.commit()

        return final_path, final_size

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(500, "Image upload failed")

    finally:
        db.close()

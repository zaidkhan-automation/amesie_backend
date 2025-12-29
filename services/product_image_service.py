# services/product_image_service.py

import os
from typing import Tuple
from fastapi import HTTPException

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
    position: int,
) -> Tuple[str, int]:
    """
    Validates, converts, compresses, and stores a product image as WEBP.

    IMPORTANT:
    - Caller MUST verify seller owns product_id before calling this.
    - This service only handles image processing + storage.

    Returns:
        (image_path, final_size_bytes)
    """

    # 1️⃣ Upload size guard (pre-conversion)
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Image too large. Max upload size is 2MB.",
        )

    # 2️⃣ Convert → WEBP
    try:
        webp_bytes, final_size, mime = process_image_to_webp(raw_bytes)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file.",
        )

    # 3️⃣ Enforce WEBP + compressed size
    if mime != "image/webp":
        raise HTTPException(
            status_code=400,
            detail="Image conversion failed.",
        )

    if final_size > MAX_FINAL_WEBP_BYTES:
        raise HTTPException(
            status_code=400,
            detail="Compressed image exceeds 500KB limit.",
        )

    # 4️⃣ Build safe storage path
    folder_path = os.path.normpath(
        os.path.join(
            BASE_STORAGE_PATH,
            f"seller_{seller_id}",
            f"product_{product_id}",
        )
    )

    os.makedirs(folder_path, exist_ok=True)

    filename = f"{position}.webp"
    final_path = os.path.join(folder_path, filename)
    temp_path = final_path + ".tmp"

    # 5️⃣ Atomic write (temp → rename)
    try:
        with open(temp_path, "wb") as f:
            f.write(webp_bytes)

        os.replace(temp_path, final_path)
    except Exception:
        # Clean up temp file if anything fails
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=500,
            detail="Failed to store image.",
        )

    return final_path, final_size

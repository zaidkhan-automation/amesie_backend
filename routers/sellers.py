from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import uuid
import re
from datetime import datetime

from core.database import get_db
from core.redis import redis_client
from core.logging_config import get_logger

from db import models
from schemas import schemas
from services.auth import get_current_user
from services.notification_service import notify_order_status_update

router = APIRouter()
logger = get_logger("seller")

# ─────────────────────────────────────────────
# FILE UPLOAD CONFIG
# ─────────────────────────────────────────────
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024
UPLOAD_ROOT = "static/uploads"

PROFILE_DIR = f"{UPLOAD_ROOT}/profile_pictures"
PRODUCT_DIR = f"{UPLOAD_ROOT}/product_images"

os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(PRODUCT_DIR, exist_ok=True)


async def save_upload_file(file: UploadFile, folder: str) -> str:
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")

    name = f"{uuid.uuid4()}{ext}"
    path = f"{folder}/{name}"

    with open(path, "wb") as f:
        f.write(content)

    return f"/{path}"


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
def get_current_seller(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != models.UserRole.SELLER:
        raise HTTPException(403, "Seller access required")

    seller = db.query(models.Seller).filter_by(user_id=user.id).first()
    if not seller:
        raise HTTPException(404, "Seller profile not found")

    return seller


# ─────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────
@router.post("/products", response_model=schemas.Product)
def create_product(
    payload: schemas.ProductCreate,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    # 🔒 SKU MUST BE GENERATED SERVER-SIDE
    def _slugify(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9]+", "-", text)
        return text.strip("-")

    slug = _slugify(payload.name)
    sku = f"AUTO-{seller.id}-{slug}-{uuid.uuid4().hex[:6].upper()}"

    # remove forbidden fields from payload
    data = payload.dict(exclude={"seller_id", "sku"})

    product = models.Product(
        **data,
        sku=sku,               # ✅ FIXED
        seller_id=seller.id,   # single source of truth
        is_active=True,
        is_deleted=False,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    # 🔥 CACHE INVALIDATION (UNCHANGED)
    try:
        for key in redis_client.scan_iter("products:list*"):
            redis_client.delete(key)
    except Exception:
        pass

    return product


@router.put("/products/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    payload: schemas.ProductUpdate,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.seller_id == seller.id,
        models.Product.is_deleted.is_(False),
    ).first()

    if not product:
        raise HTTPException(404, "Product not found")

    for k, v in payload.dict(exclude_unset=True).items():
        setattr(product, k, v)

    db.commit()
    db.refresh(product)

    try:
        redis_client.delete(f"product:{product_id}")
        redis_client.delete_pattern("products:list:*")
    except Exception as e:
        logger.warning(f"Redis invalidate failed: {e}")

    return product


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter_by(
        id=product_id,
        seller_id=seller.id,
    ).first()

    if not product:
        raise HTTPException(404, "Product not found")

    product.is_deleted = True
    product.is_active = False
    product.deleted_at = datetime.utcnow()

    db.commit()

    try:
        redis_client.delete(f"product:{product_id}")
        redis_client.delete_pattern("products:list:*")
    except Exception as e:
        logger.warning(f"Redis invalidate failed: {e}")

    return {"message": "Product deleted"}

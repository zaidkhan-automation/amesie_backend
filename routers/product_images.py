import logging
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from db import models
from services.product_image_service import handle_product_image_upload
from routers.sellers import get_current_seller
from schemas import schemas


router = APIRouter(tags=["Product Images"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# UPLOAD PRODUCT IMAGE (SELLER ONLY)
# ─────────────────────────────────────────────
@router.post(
    "/api/products/{product_id}/images",
    response_model=schemas.ProductImage,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id,
            models.Product.seller_id == seller.id,
            models.Product.is_deleted.is_(False),
            models.Product.is_active.is_(True),
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied",
        )

    raw_bytes = await file.read()

    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images allowed",
        )

    if len(raw_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image too large. Max size is 5MB",
        )

    try:
        path, _ = handle_product_image_upload(
            seller_id=seller.id,
            product_id=product_id,
            raw_bytes=raw_bytes,
        )
    except Exception:
        logger.exception("Image upload failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed",
        )

    max_order = (
        db.query(func.max(models.ProductImage.display_order))
        .filter(models.ProductImage.product_id == product_id)
        .scalar()
        or 0
    )

    product_image = models.ProductImage(
        product_id=product_id,
        image_url=path,
        display_order=max_order + 1,
        is_primary=(max_order == 0),
    )

    db.add(product_image)
    db.commit()
    db.refresh(product_image)

    return product_image


# ─────────────────────────────────────────────
# GET PRODUCT IMAGES (PUBLIC)
# ─────────────────────────────────────────────
@router.get(
    "/api/products/{product_id}/images",
    response_model=List[schemas.ProductImage],
)
def get_product_images(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id,
            models.Product.is_deleted.is_(False),
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    images = (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .order_by(models.ProductImage.display_order.asc())
        .all()
    )

    return images

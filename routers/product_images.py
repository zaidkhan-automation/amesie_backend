import logging
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from db import models
from services.product_image_service import handle_product_image_upload
from routers.sellers import get_current_seller
from schemas import schemas


router = APIRouter(tags=["Product Images"])
logger = logging.getLogger(__name__)


@router.post(
    "/api/products/{product_id}/images",
    response_model=schemas.ProductImage,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
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
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    raw_bytes = await file.read()

    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    handle_product_image_upload(
        db=db,
        seller_id=seller.id,
        product_id=product_id,
        raw_bytes=raw_bytes,
    )

    image = (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .order_by(models.ProductImage.id.desc())
        .first()
    )

    return image


@router.get(
    "/api/products/{product_id}/images",
    response_model=List[schemas.ProductImage],
    include_in_schema=False
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
        raise HTTPException(status_code=404, detail="Product not found")

    images = (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .order_by(models.ProductImage.display_order.asc())
        .all()
    )

    return images

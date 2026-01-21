# routers/seller_product_image.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from services.product_image_service import handle_product_image_upload
from routers.sellers import get_current_seller
from db import models

router = APIRouter(
    prefix="/seller/products",
    tags=["Seller Product Images"],
)


@router.post("/{product_id}/images")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    """
    Upload product image for seller-owned product.
    Seller auth is already enforced by get_current_seller.
    """

    # 🔒 Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files allowed")

    raw_bytes = await file.read()

    # 🔒 Ensure product belongs to this seller
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

    image_path, size = handle_product_image_upload(
        seller_id=seller.id,
        product_id=product_id,
        raw_bytes=raw_bytes,
    )

    return {
        "success": True,
        "image_url": image_path,
        "size_bytes": size,
    }

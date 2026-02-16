from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid
import re

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user
from services.product_vector_ingest import index_product
from services.product_image_service import handle_product_image_upload

router = APIRouter()


def get_current_seller(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != models.UserRole.SELLER:
        raise HTTPException(status_code=403, detail="Seller access required")

    seller = (
        db.query(models.Seller)
        .filter(models.Seller.user_id == user.id)
        .first()
    )

    if not seller:
        raise HTTPException(status_code=404, detail="Seller profile not found")

    return seller


@router.get("/products")
def get_my_products(
    skip: int = 0,
    limit: int = 20,
    is_active: Optional[bool] = None,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    query = (
        db.query(models.Product)
        .options(selectinload(models.Product.images))
        .filter(
            models.Product.seller_id == seller.id,
            models.Product.is_deleted.is_(False),
        )
    )

    if is_active is not None:
        query = query.filter(models.Product.is_active == is_active)

    return query.offset(skip).limit(limit).all()


@router.post("/products", response_model=schemas.Product)
async def create_product(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    stock_quantity: int = Form(0),
    category: str = Form(...),
    images: List[UploadFile] = File([]),
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db),
):

    category_obj = (
        db.query(models.Category)
        .filter(models.Category.name.ilike(category.strip()))
        .first()
    )

    if not category_obj:
        raise HTTPException(status_code=400, detail="Invalid category")

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    sku = f"AUTO-{seller.id}-{slug}-{uuid.uuid4().hex[:6].upper()}"

    product = models.Product(
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category_id=category_obj.id,
        sku=sku,
        seller_id=seller.id,
        is_active=True,
        is_deleted=False,
    )

    try:
        db.add(product)
        db.flush()  # ⬅️ get product.id WITHOUT committing yet

        # 🔥 Process images in SAME DB transaction
        for file in images:
            raw_bytes = await file.read()
            if raw_bytes:
                handle_product_image_upload(
                    db=db,
                    seller_id=seller.id,
                    product_id=product.id,
                    raw_bytes=raw_bytes,
                )

        db.commit()  # ⬅️ ONE SINGLE COMMIT for product + images

        index_product(db, product.id)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="SKU collision")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    product = (
        db.query(models.Product)
        .options(selectinload(models.Product.images))
        .filter(models.Product.id == product.id)
        .first()
    )

    return product


@router.put("/products/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    payload: schemas.ProductUpdate,
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

    update_data = payload.model_dump(exclude_unset=True)

    if "category" in update_data:
        category_obj = (
            db.query(models.Category)
            .filter(models.Category.name.ilike(update_data["category"].strip()))
            .first()
        )

        if not category_obj:
            raise HTTPException(status_code=400, detail="Invalid category")

        product.category_id = category_obj.id
        del update_data["category"]

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    index_product(db, product.id)

    return product


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
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

    product.is_deleted = True
    product.is_active = False
    db.commit()

    index_product(db, product.id)

    return {"message": "Product deleted successfully"}

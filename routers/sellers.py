from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
import uuid
import re

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import get_current_user
from services.product_vector_ingest import index_product

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
    is_active: bool | None = None,
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
def create_product(
    payload: schemas.ProductCreate,
    seller: models.Seller = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    category = (
        db.query(models.Category)
        .filter(models.Category.name.ilike(payload.category.strip()))
        .first()
    )

    if not category:
        raise HTTPException(status_code=400, detail="Invalid category")

    slug = re.sub(r"[^a-z0-9]+", "-", payload.name.lower()).strip("-")
    sku = f"AUTO-{seller.id}-{slug}-{uuid.uuid4().hex[:6].upper()}"

    product = models.Product(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        category_id=category.id,
        sku=sku,
        seller_id=seller.id,
        is_active=True,
        is_deleted=False,
    )

    try:
        db.add(product)
        db.commit()
        db.refresh(product)
        index_product(db, product.id)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="SKU collision")

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

    update_data = payload.dict(exclude_unset=True)

    if "category" in update_data:
        category = (
            db.query(models.Category)
            .filter(models.Category.name.ilike(update_data["category"].strip()))
            .first()
        )

        if not category:
            raise HTTPException(status_code=400, detail="Invalid category")

        product.category_id = category.id
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

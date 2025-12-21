from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, text

from core.database import get_db
from db import models
from schemas import schemas
from services.graph_service import get_similar_products
from services.auth import get_current_user

router = APIRouter()
@router.get("/debug/graph")
def debug_graph(db: Session = Depends(get_db)):
    from services.graph_debugger import run_graph_debugger
    run_graph_debugger(db, product_id=13)
    return {"ok": True, "msg": "Graph debugger executed. Check logs."}
# ─────────────────────────────────────────────
# PRODUCT RECOMMENDATIONS (GRAPH / AGE)
# ─────────────────────────────────────────────
@router.get("/{product_id}/recommendations")
def product_recommendations(
    product_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    # ✅ db MUST be first argument
    return get_similar_products(db=db, product_id=product_id, limit=limit)
# ─────────────────────────────────────────────
# PRODUCT LISTING
# ─────────────────────────────────────────────
@router.get("/", response_model=List[schemas.Product])
def get_products(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[int] = None,
    include_children: bool = True,
    seller_id: Optional[int] = None,
    is_veg: Optional[bool] = None,
    is_live: Optional[bool] = True,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Product).filter(
        models.Product.is_active == True,
        models.Product.is_deleted == False,
    )

    if category_id:
        if include_children:
            child_ids = db.execute(
                text("SELECT id FROM product_categories WHERE parent_id = :pid"),
                {"pid": category_id},
            ).fetchall()

            ids = [category_id] + [c.id for c in child_ids]
            query = query.filter(models.Product.category_id.in_(ids))
        else:
            query = query.filter(models.Product.category_id == category_id)

    if seller_id:
        query = query.filter(models.Product.seller_id == seller_id)

    if is_veg is not None:
        query = query.filter(models.Product.is_veg == is_veg)

    if is_live is not None:
        query = query.filter(models.Product.is_live == is_live)

    if search:
        query = query.filter(
            or_(
                models.Product.name.ilike(f"%{search}%"),
                models.Product.description.ilike(f"%{search}%"),
                models.Product.sku.ilike(f"%{search}%"),
            )
        )

    return query.offset(skip).limit(limit).all()


# ─────────────────────────────────────────────
# SINGLE PRODUCT
# ─────────────────────────────────────────────
@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id,
            models.Product.is_active == True,
            models.Product.is_deleted == False,
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product

from typing import List, Optional
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, text

from core.database import get_db
from core.redis import redis_client
from db import models
from schemas import schemas

from services.recommendation_service import (
    get_product_recommendations,
    get_nearby_recommended_products,
)

from services.auth import get_current_user

router = APIRouter()

# ─────────────────────────────────────────────
# GRAPH DEBUG (INTERNAL ONLY)
# ─────────────────────────────────────────────
@router.get("/debug/graph")
def debug_graph(db: Session = Depends(get_db)):
    from services.graph_debugger import run_graph_debugger
    run_graph_debugger(db, product_id=13)
    return {"ok": True, "msg": "Graph debugger executed. Check logs."}


# ─────────────────────────────────────────────
# NEARBY RECOMMENDATIONS
# ─────────────────────────────────────────────
@router.get("/nearby/recommendations")
def nearby_recommendations(
    radius: int = 5000,
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_nearby_recommended_products(
        db=db,
        buyer_id=current_user.id,
        radius=radius,
        limit=limit,
    )


# ─────────────────────────────────────────────
# NEARBY PRODUCTS (REDIS CACHED)
# ─────────────────────────────────────────────
@router.get("/nearby")
def nearby_products(
    lat: float,
    lng: float,
    radius: int = 3000,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    cache_key = f"products:nearby:{lat}:{lng}:{radius}:{limit}"

    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    sql = text("""
        SELECT
            p.id            AS product_id,
            p.name          AS product_name,
            p.price         AS price,
            p.seller_id     AS seller_id,
            s.store_name    AS store_name,
            ST_Distance(
                s.location,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            ) AS distance_meters
        FROM sellers s
        JOIN products p ON p.seller_id = s.id
        WHERE
            s.is_active = true
            AND p.is_active = true
            AND p.is_deleted IS NOT TRUE
            AND s.location IS NOT NULL
            AND ST_DWithin(
                s.location,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                :radius
            )
        ORDER BY distance_meters, p.id DESC
        LIMIT :limit
    """)

    rows = db.execute(
        sql,
        {"lat": lat, "lng": lng, "radius": radius, "limit": limit},
    ).fetchall()

    response = {
        "lat": lat,
        "lng": lng,
        "radius": radius,
        "count": len(rows),
        "items": [
            {
                "product_id": r.product_id,
                "name": r.product_name,
                "price": float(r.price),
                "seller_id": r.seller_id,
                "store_name": r.store_name,
                "distance_meters": float(r.distance_meters),
            }
            for r in rows
        ],
    }

    try:
        redis_client.setex(cache_key, 30, json.dumps(response))
    except Exception as e:
        print("REDIS SET ERROR (nearby):", e)

    return response


# ─────────────────────────────────────────────
# PRODUCT RECOMMENDATIONS
# ─────────────────────────────────────────────
@router.get("/{product_id}/recommendations")
def product_recommendations(
    product_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    return get_product_recommendations(
        db=db,
        product_id=product_id,
        limit=limit,
    )


# ─────────────────────────────────────────────
# PRODUCT LISTING (REDIS CACHED) ✅ FIXED
# ─────────────────────────────────────────────
@router.get("/")
def get_products(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[int] = None,
    include_children: bool = True,
    seller_id: Optional[int] = None,
    is_veg: Optional[bool] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    cache_key = (
        f"products:list:{skip}:{limit}:{category_id}:"
        f"{include_children}:{seller_id}:{is_veg}:{is_active}:{search}"
    )

    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    query = db.query(models.Product).filter(
        models.Product.is_deleted.is_(False),
    )

    if is_active is not None:
        query = query.filter(models.Product.is_active == is_active)

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

    if search:
        query = query.filter(
            or_(
                models.Product.name.ilike(f"%{search}%"),
                models.Product.description.ilike(f"%{search}%"),
                models.Product.sku.ilike(f"%{search}%"),
            )
        )

    results = query.offset(skip).limit(limit).all()

    # ✅ Pydantic v2 FIX (ONLY CHANGE)
    data = [
        schemas.Product.model_validate(p).model_dump()
        for p in results
    ]

    try:
        redis_client.setex(cache_key, 60, json.dumps(data, default=str))
    except Exception as e:
        print("REDIS SET ERROR (list):", e)

    return data


# ─────────────────────────────────────────────
# SINGLE PRODUCT (REDIS CACHED)
# ─────────────────────────────────────────────
@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    cache_key = f"product:{product_id}"

    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id,
            models.Product.is_active.is_(True),
            models.Product.is_deleted.is_(False),
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = schemas.Product.model_validate(product).model_dump()

    try:
        redis_client.setex(cache_key, 120, json.dumps(data, default=str))
    except Exception as e:
        print("REDIS SET ERROR (single):", e)

    return data

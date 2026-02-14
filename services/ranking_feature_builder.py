# services/ranking_feature_builder.py

from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from db import models


def build_features(
    db: Session,
    query: str,
    candidate_products: List[Dict],
) -> List[Dict]:

    product_ids = [p["id"] for p in candidate_products]

    if not product_ids:
        return []

    # Load products
    products = (
        db.query(models.Product)
        .filter(models.Product.id.in_(product_ids))
        .all()
    )

    product_map = {p.id: p for p in products}

    # Aggregate search logs
    logs = (
        db.query(
            models.SearchLog.product_id,
            func.count(models.SearchLog.id).label("impressions"),
            func.sum(
                case((models.SearchLog.clicked == True, 1), else_=0)
            ).label("clicks"),
            func.sum(
                case((models.SearchLog.purchased == True, 1), else_=0)
            ).label("purchases"),
        )
        .filter(models.SearchLog.product_id.in_(product_ids))
        .group_by(models.SearchLog.product_id)
        .all()
    )

    log_map = {
        row.product_id: {
            "impressions": row.impressions or 0,
            "clicks": row.clicks or 0,
            "purchases": row.purchases or 0,
        }
        for row in logs
    }

    features = []

    for item in candidate_products:
        product_id = item["id"]
        vector_score = float(item.get("score", 0))

        product = product_map.get(product_id)
        if not product:
            continue

        price = float(product.price or 0)
        stock = int(product.stock_quantity or 0)

        seller_rating = (
            float(product.seller.rating or 0)
            if product.seller else 0
        )

        seller_total_sales = (
            int(product.seller.total_sales or 0)
            if product.seller and hasattr(product.seller, "total_sales")
            else 0
        )

        log_data = log_map.get(product_id, {})
        impressions = log_data.get("impressions", 0)
        clicks = log_data.get("clicks", 0)
        purchases = log_data.get("purchases", 0)

        ctr = (clicks / impressions) if impressions > 0 else 0
        conversion = (purchases / impressions) if impressions > 0 else 0

        feature_row = {
            "product_id": product_id,
            "vector_score": vector_score,
            "price": price,
            "stock_quantity": stock,
            "seller_rating": seller_rating,
            "seller_total_sales": seller_total_sales,
            "ctr": ctr,
            "conversion": conversion,
        }

        features.append(feature_row)

    return features


def rank_results(
    db: Session,
    query: str,
    candidate_products: List[Dict],
) -> List[Dict]:

    features = build_features(db, query, candidate_products)

    # Weighted ranking formula
    for f in features:
        stock_boost = min(f["stock_quantity"], 100) / 100

        f["final_score"] = (
            0.5 * f["vector_score"]
            + 0.2 * f["seller_rating"]
            + 0.15 * f["ctr"]
            + 0.1 * f["conversion"]
            + 0.05 * stock_boost
        )

    # Sort descending
    features.sort(key=lambda x: x["final_score"], reverse=True)

    ranked_ids = [f["product_id"] for f in features]

    ranked_products = []
    product_map = {p["id"]: p for p in candidate_products}

    for pid in ranked_ids:
        if pid in product_map:
            ranked_products.append(product_map[pid])

    return ranked_products

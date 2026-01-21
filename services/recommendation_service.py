import os
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.logging_config import get_logger
from services.graph_service import get_similar_products
from db import models

logger = get_logger("recommendation")

# ─────────────────────────────────────────────
# FEATURE FLAG
# ─────────────────────────────────────────────
GRAPH_ENABLED = os.getenv("GRAPH_ENABLED", "true").lower() == "true"


# ─────────────────────────────────────────────
# STEP-1: PRODUCT → PRODUCT RECOMMENDATION
# ─────────────────────────────────────────────
def get_product_recommendations(
    db: Session,
    product_id: int,
    limit: int = 5,
):
    """
    Single-product recommendation.
    Graph → fallback
    """

    logger.info(
        f"[RECO] Start | product_id={product_id}, limit={limit}, graph_enabled={GRAPH_ENABLED}"
    )

    if GRAPH_ENABLED:
        try:
            graph_results = get_similar_products(
                db=db,
                product_id=product_id,
                limit=limit,
            )

            if graph_results:
                logger.info(f"[RECO] Graph success | count={len(graph_results)}")
                return graph_results

            logger.warning("[RECO] Graph empty → fallback")

        except Exception:
            logger.exception("[RECO] Graph failed → fallback")

    return fallback_recommendations(db, product_id, limit)


def fallback_recommendations(
    db: Session,
    product_id: int,
    limit: int,
):
    """
    Same-category fallback
    """

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
        return []

    items = (
        db.query(models.Product)
        .filter(
            models.Product.category_id == product.category_id,
            models.Product.id != product_id,
            models.Product.is_active.is_(True),
            models.Product.is_deleted.is_(False),
        )
        .order_by(models.Product.id.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "pid": p.id,
            "name": p.name,
            "price": float(p.price),
            "weight": 0.0,
        }
        for p in items
    ]


# ─────────────────────────────────────────────
# STEP-2: LOCATION + GRAPH RECOMMENDATION
# ─────────────────────────────────────────────
def get_nearby_recommended_products(
    db: Session,
    buyer_id: int,
    radius: int = 5000,
    limit: int = 20,
):
    """
    Buyer-location based recommendations.

    Flow:
    buyer location
      → nearby sellers (PostGIS)
      → products
      → graph score
      → final rank
    """

    logger.info(f"[RECO-NEARBY] buyer_id={buyer_id}, radius={radius}")

    # 1️⃣ buyer location
    buyer = db.execute(
        text("""
        SELECT location
        FROM users
        WHERE id = :uid
          AND location IS NOT NULL
        """),
        {"uid": buyer_id},
    ).fetchone()

    if not buyer:
        logger.warning("[RECO-NEARBY] Buyer location missing")
        return []

    # 2️⃣ nearby products
    rows = db.execute(
        text("""
        SELECT
            p.id   AS product_id,
            p.name,
            p.price,
            s.store_name,
            ST_Distance(
                s.location,
                :buyer_loc
            ) AS distance
        FROM sellers s
        JOIN products p ON p.seller_id = s.id
        WHERE
            s.is_active = true
            AND p.is_active = true
            AND p.is_deleted = false
            AND ST_DWithin(s.location, :buyer_loc, :radius)
        """),
        {
            "buyer_loc": buyer.location,
            "radius": radius,
        },
    ).mappings().all()

    if not rows:
        return []

    # 3️⃣ graph scores (optional)
    graph_scores = {}
    if GRAPH_ENABLED:
        try:
            product_ids = [r["product_id"] for r in rows]
            graph_scores = _get_graph_scores(db, product_ids)
        except Exception:
            logger.exception("[RECO-NEARBY] Graph score fetch failed")

    # 4️⃣ scoring
    results = []
    for r in rows:
        geo_score = max(0.0, 1 - (r["distance"] / radius))
        graph_score = graph_scores.get(r["product_id"], 0.0)

        final_score = (0.6 * geo_score) + (0.4 * graph_score)

        results.append({
            "product_id": r["product_id"],
            "name": r["name"],
            "price": float(r["price"]),
            "store_name": r["store_name"],
            "distance_meters": float(r["distance"]),
            "geo_score": round(geo_score, 3),
            "graph_score": round(graph_score, 3),
            "final_score": round(final_score, 3),
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:limit]


# ─────────────────────────────────────────────
# INTERNAL GRAPH SCORE HELPER
# ─────────────────────────────────────────────
def _get_graph_scores(db: Session, product_ids: list[int]) -> dict:
    """
    Max SIMILAR edge weight per product
    """

    if not product_ids:
        return {}

    id_list = ",".join(map(str, product_ids))

    rows = db.execute(
        text(f"""
        SELECT src, dst, weight
        FROM cypher(
          'amesie_graph',
          $$
            MATCH (a:Product)-[r:SIMILAR]->(b:Product)
            WHERE b.pid IN [{id_list}]
            RETURN a.pid AS src, b.pid AS dst, r.weight AS weight
          $$
        ) AS (src int, dst int, weight float)
        """)
    ).fetchall()

    scores = {}
    for _, dst, w in rows:
        scores[dst] = max(scores.get(dst, 0.0), w)

    return scores

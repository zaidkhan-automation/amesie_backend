from typing import Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from services.vector_service import search_products
from services.ranking_feature_builder import rank_results
from db import models

router = APIRouter()


@router.get("/search")
def search_products_api(
    q: str = Query(...),
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db),
):
    # Step 1: Vector search
    results = search_products(
        query=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
    )

    if not results:
        return []

    # Step 2: Ranking layer
    ranked_results = rank_results(
        db,
        q,
        results,
    )

    # Step 3: Log impressions for training
    for item in ranked_results:
        try:
            log = models.SearchLog(
                query=q,
                product_id=item["id"],
                clicked=False,
                added_to_cart=False,
                purchased=False,
            )
            db.add(log)
        except Exception:
            continue

    db.commit()

    return ranked_results


@router.post("/search/click")
def track_search_click(
    query: str,
    product_id: int,
    db: Session = Depends(get_db),
):
    log = (
        db.query(models.SearchLog)
        .filter(
            models.SearchLog.query == query,
            models.SearchLog.product_id == product_id,
        )
        .order_by(models.SearchLog.id.desc())
        .first()
    )

    if not log:
        return {"message": "No search log found"}

    log.clicked = True
    db.commit()

    return {"message": "Click tracked"}

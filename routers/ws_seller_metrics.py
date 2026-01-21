import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from core.database import SessionLocal
from db import models
from datetime import datetime

router = APIRouter()

def get_metrics(db: Session, seller_id: int):
    total_products = db.query(models.Product).filter(
        models.Product.seller_id == seller_id
    ).count()

    active_products = db.query(models.Product).filter(
        models.Product.seller_id == seller_id,
        models.Product.is_active == True
    ).count()

    out_of_stock = db.query(models.Product).filter(
        models.Product.seller_id == seller_id,
        models.Product.stock <= 0
    ).count()

    total_orders = db.query(models.Order).filter(
        models.Order.seller_id == seller_id
    ).count()

    today_orders = db.query(models.Order).filter(
        models.Order.seller_id == seller_id,
        models.Order.created_at >= datetime.utcnow().date()
    ).count()

    revenue_total = db.query(models.Order).filter(
        models.Order.seller_id == seller_id,
        models.Order.status == "completed"
    ).with_entities(models.func.sum(models.Order.total_amount)).scalar() or 0

    revenue_today = db.query(models.Order).filter(
        models.Order.seller_id == seller_id,
        models.Order.status == "completed",
        models.Order.created_at >= datetime.utcnow().date()
    ).with_entities(models.func.sum(models.Order.total_amount)).scalar() or 0

    return {
        "seller_id": seller_id,
        "total_products": total_products,
        "active_products": active_products,
        "out_of_stock": out_of_stock,
        "total_orders": total_orders,
        "today_orders": today_orders,
        "revenue_today": revenue_today,
        "revenue_total": revenue_total,
        "last_updated": datetime.utcnow().isoformat(),
    }

@router.websocket("/ws/seller/metrics/{seller_id}")
async def seller_metrics_ws(ws: WebSocket, seller_id: int):
    await ws.accept()
    db = SessionLocal()

    try:
        while True:
            data = get_metrics(db, seller_id)
            await ws.send_json(data)
            await asyncio.sleep(5)  # 🔁 refresh interval
    except WebSocketDisconnect:
        print(f"WS disconnected for seller {seller_id}")
    finally:
        db.close()

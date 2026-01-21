import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from core.database import SessionLocal
from services.seller_metrics import get_seller_metrics

router = APIRouter()


@router.websocket("/ws/seller/metrics/{seller_id}")
async def seller_metrics_ws(ws: WebSocket, seller_id: int):
    await ws.accept()
    db: Session = SessionLocal()

    try:
        while True:
            try:
                metrics = get_seller_metrics(db, seller_id)

                # ✅ Final payload (direct + clean)
                payload = {
                    "seller_id": seller_id,
                    "total_products": metrics.get("total_products", 0),
                    "active_products": metrics.get("active_products", 0),
                    "inactive_products": metrics.get("inactive_products", 0),
                    "out_of_stock": metrics.get("out_of_stock", 0),
                    "low_stock": metrics.get("low_stock", 0),
                    "orders_today": metrics.get("orders_today", 0),
                    "revenue_today": metrics.get("revenue_today", 0.0),
                }

                await ws.send_json(payload)

            except Exception as e:
                # ⚠️ Never kill WS loop on metric failure
                await ws.send_json({
                    "seller_id": seller_id,
                    "error": "metrics_fetch_failed",
                    "detail": str(e),
                })

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        print(f"[WS] Seller metrics disconnected | seller_id={seller_id}")

    finally:
        db.close()
        print(f"[WS] DB session closed | seller_id={seller_id}")

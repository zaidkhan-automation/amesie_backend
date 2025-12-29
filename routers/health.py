from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import get_db
from core.redis import redis_client
import redis   # <-- THIS was missing

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
def health_check():
    return {"ok": True}

@router.get("/db")
def db_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"ok": True, "db": "up"}
    except Exception as e:
        return {"ok": False, "db": "down", "error": str(e)}

@router.get("/redis")   # <-- FIXED HERE (removed extra /health)
def redis_health():
    try:
        r = redis.Redis(
            host="127.0.0.1",
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
        )
        r.ping()
        return {"redis": "ok"}
    except Exception as e:
        return {
            "redis": "error",
            "detail": str(e)
        }

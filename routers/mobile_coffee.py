# backend/routers/mobile_coffee.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(
    prefix="/api",
    tags=["mobile-coffee"],
)

class MobileCoffeeItem(BaseModel):
    id: str
    name: str
    size: str
    ml: int
    qty: int
    price: float

class MobileCoffeeOrder(BaseModel):
    items: List[MobileCoffeeItem]
    address: str
    note: Optional[str] = ""
    total: float
    createdAt: str

@router.post("/mobile-coffee-orders")
async def create_mobile_coffee_order(order: MobileCoffeeOrder):
    # TODO: yahan baad me Asim/Farhan:
    # - user_id from auth
    # - real OrderCreate call
    # - payment flow / etc
    print("📦 MOBILE COFFEE ORDER RECEIVED:", order.dict())
    return {
        "status": "ok",
        "items_count": len(order.items),
        "total": order.total,
    }

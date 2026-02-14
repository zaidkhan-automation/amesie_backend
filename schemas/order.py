# schemas/order.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class OrderItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float

    class Config:
        from_attributes = True


class Order(BaseModel):
    id: int
    user_id: int
    location_id: Optional[int]
    total_amount: float
    order_status: str
    payment_status: str
    created_at: datetime
    order_items: List[OrderItem] = []

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    location_id: Optional[int] = None

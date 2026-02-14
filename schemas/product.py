# schemas/product.py

from pydantic import BaseModel
from typing import Optional, List

class ProductImageOut(BaseModel):
    id: int
    image_url: str
    is_primary: bool
    display_order: int

    class Config:
        from_attributes = True


class Product(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    sku: str
    stock_quantity: int
    category_id: Optional[int]
    seller_id: int
    is_active: bool

    images: List[ProductImageOut] = []

    class Config:
        from_attributes = True

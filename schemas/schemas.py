from __future__ import annotations

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ENUMS

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    SELLER = "SELLER"
    CUSTOMER = "CUSTOMER"


class NotificationType(str, Enum):
    ORDER_PLACED = "order_placed"
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"
    PAYMENT_RECEIVED = "payment_received"


# AUTH

class Token(BaseModel):
    access_token: str
    token_type: str


# USER

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ADDRESS

class AddressBase(BaseModel):
    full_name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class Address(AddressBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# CATEGORY

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class Category(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# PRODUCT IMAGE

class ProductImageBase(BaseModel):
    image_url: str
    display_order: int
    is_primary: bool = False


class ProductImage(ProductImageBase):
    id: int
    product_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# PRODUCT

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int = 0
    category: str   # changed from category_id


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    category: Optional[str] = None  # changed
    is_active: Optional[bool] = None


class SellerBasic(BaseModel):
    id: int
    store_name: str
    rating: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)


class Product(ProductBase):
    id: int
    sku: str
    is_active: bool
    is_deleted: bool
    created_at: datetime

    category: Optional[Category] = None
    seller: Optional[SellerBasic] = None
    images: List[ProductImage] = []

    model_config = ConfigDict(from_attributes=True)


# CART

class CartItemBase(BaseModel):
    product_id: int
    quantity: int


class CartItemCreate(CartItemBase):
    pass


class CartItem(CartItemBase):
    id: int
    user_id: int
    created_at: datetime
    product: Product

    model_config = ConfigDict(from_attributes=True)


# WISHLIST

class WishlistItemBase(BaseModel):
    product_id: int


class WishlistItemCreate(WishlistItemBase):
    pass


class WishlistItem(WishlistItemBase):
    id: int
    user_id: int
    created_at: datetime
    product: Product

    model_config = ConfigDict(from_attributes=True)


# ORDERS

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime
    product: Optional[Product] = None

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    location_id: int


class OrderCreate(OrderBase):
    pass


class Order(OrderBase):
    id: int
    user_id: int
    total_amount: float
    order_status: str
    created_at: datetime

    order_items: List[OrderItem] = []

    model_config = ConfigDict(from_attributes=True)


# NOTIFICATIONS

class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: NotificationType
    order_id: Optional[int] = None


class NotificationCreate(NotificationBase):
    user_id: int


class Notification(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

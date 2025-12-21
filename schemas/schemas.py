from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
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

# User schemas
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

    class Config:
        orm_mode = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    class Config:
        orm_mode = True

# Product schemas
class ProductImageBase(BaseModel):
    image_url: str
    alt_text: Optional[str] = None
    display_order: int = 0

class ProductImageCreate(ProductImageBase):
    pass

class ProductImage(ProductImageBase):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    sku: str
    image_url: Optional[str] = None  # Keep for backward compatibility
    stock_quantity: int = 0

    # Shipping information
    weight: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    shipping_info: Optional[str] = None

    category_id: int
    seller_id: Optional[int] = None

class ProductCreate(ProductBase):
    images: Optional[List[ProductImageCreate]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    sku: Optional[str] = None
    stock_quantity: Optional[int] = None
    weight: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    shipping_info: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None

# Forward declaration for Seller
class SellerBasic(BaseModel):
    id: int
    store_name: str
    store_logo_url: Optional[str] = None
    rating: float = 0.0

    class Config:
        orm_mode = True

class Product(ProductBase):
    id: int
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    category: Optional[Category] = None
    seller: Optional[SellerBasic] = None
    images: List[ProductImage] = []

    class Config:
        orm_mode = True

# Address schemas
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

    class Config:
        orm_mode = True

# Cart schemas
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

    class Config:
        orm_mode = True

# Order schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    product: Product

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    shipping_address: str

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    user_id: int
    total_amount: float
    payment_id: Optional[str] = None
    payment_status: str
    order_status: str
    created_at: datetime
    order_items: List[OrderItem] = []

    class Config:
        orm_mode = True

# Review schemas
class ReviewBase(BaseModel):
    product_id: int
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class Review(ReviewBase):
    id: int
    user_id: int
    created_at: datetime
    user: User

    class Config:
        orm_mode = True

# Wishlist schemas
class WishlistItemBase(BaseModel):
    product_id: int

class WishlistItemCreate(WishlistItemBase):
    pass

class WishlistItem(WishlistItemBase):
    id: int
    user_id: int
    created_at: datetime
    product: Product

    class Config:
        orm_mode = True

# Seller schemas
class SellerBase(BaseModel):
    store_name: str
    store_description: Optional[str] = None
    store_logo_url: Optional[str] = None
    profile_picture_url: Optional[str] = None
    business_license: Optional[str] = None

    # Address fields
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    # Bank account details
    account_holder_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None

    # Tax information
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    vat_number: Optional[str] = None
    tax_id: Optional[str] = None

    # Keep for backward compatibility
    store_address: Optional[str] = None

class SellerCreate(SellerBase):
    pass

class SellerUpdate(BaseModel):
    store_name: Optional[str] = None
    store_description: Optional[str] = None
    store_logo_url: Optional[str] = None
    profile_picture_url: Optional[str] = None
    business_license: Optional[str] = None

    # Address fields
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    # Bank account details
    account_holder_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None

    # Tax information
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    vat_number: Optional[str] = None
    tax_id: Optional[str] = None

    store_address: Optional[str] = None

class Seller(SellerBase):
    id: int
    user_id: int
    is_verified: bool
    is_active: bool
    total_sales: float
    rating: float
    created_at: datetime
    updated_at: datetime
    user: User

    class Config:
        orm_mode = True

# Image upload schemas
class ImageUploadResponse(BaseModel):
    image_url: str
    message: str

# Notification schemas
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

    class Config:
        orm_mode = True

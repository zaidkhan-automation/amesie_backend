from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# USER SCHEMAS
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# AUTH / TOKEN
# ─────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# ─────────────────────────────────────────────
# CATEGORY
# ─────────────────────────────────────────────

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# PRODUCT IMAGES
# ─────────────────────────────────────────────

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

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    stock_quantity: int = 0

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


# ─────────────────────────────────────────────
# SELLER (BASIC)
# ─────────────────────────────────────────────

class SellerBasic(BaseModel):
    id: int
    store_name: str
    store_logo_url: Optional[str] = None
    rating: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# ADDRESS
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# CART
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# ORDERS
# ─────────────────────────────────────────────

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderItem(OrderItemBase):
    id: int
    order_id: int
    product: Product

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    shipping_address: str
    location_id: int


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

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# REVIEWS
# ─────────────────────────────────────────────

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

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# WISHLIST
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# SELLER (FULL)
# ─────────────────────────────────────────────

class SellerBase(BaseModel):
    store_name: str
    store_description: Optional[str] = None
    store_logo_url: Optional[str] = None
    profile_picture_url: Optional[str] = None
    business_license: Optional[str] = None

    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    account_holder_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None

    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    vat_number: Optional[str] = None
    tax_id: Optional[str] = None

    store_address: Optional[str] = None


class SellerCreate(SellerBase):
    pass


class SellerUpdate(BaseModel):
    store_name: Optional[str] = None
    store_description: Optional[str] = None
    store_logo_url: Optional[str] = None
    profile_picture_url: Optional[str] = None
    business_license: Optional[str] = None

    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    account_holder_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None

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
    rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    user: User

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# IMAGE UPLOAD
# ─────────────────────────────────────────────

class ImageUploadResponse(BaseModel):
    image_url: str
    message: str


# ─────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────

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

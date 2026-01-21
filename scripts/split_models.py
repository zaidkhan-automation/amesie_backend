# scripts/split_models.py
import os
from textwrap import dedent

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "db", "models")

os.makedirs(MODELS_DIR, exist_ok=True)

COMMON_IMPORTS = dedent("""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum
""").strip()

FILES = {
    "otp_verification.py": """
class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    otp_hash = Column(String, nullable=False)
    purpose = Column(String, nullable=False, default="auth")
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    last_sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
""",

    "user.py": """
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    SELLER = "SELLER"
    CUSTOMER = "CUSTOMER"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
""",

    "category.py": """
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    image_url = Column(String)

    products = relationship("Product", back_populates="category")
""",

    "product.py": """
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    sku = Column(String, unique=True, nullable=False)
    stock_quantity = Column(Integer, default=0)

    category_id = Column(Integer, ForeignKey("categories.id"))
    seller_id = Column(Integer, ForeignKey("sellers.id"))

    created_at = Column(DateTime, server_default=func.now())

    category = relationship("Category", back_populates="products")
    seller = relationship("Seller", back_populates="products")
""",

    "order.py": """
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float, nullable=False)
    order_status = Column(String, default="pending")
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
    order_items = relationship("OrderItem", back_populates="order")
""",

    "order_item.py": """
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Float)

    order = relationship("Order", back_populates="order_items")
    product = relationship("Product")
""",

    "seller.py": """
class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    store_name = Column(String, nullable=False)

    products = relationship("Product", back_populates="seller")
""",

    "notification.py": """
class NotificationType(str, enum.Enum):
    ORDER_PLACED = "order_placed"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(Text)
    notification_type = Column(Enum(NotificationType))
    created_at = Column(DateTime, server_default=func.now())
"""
}

# Write model files
for fname, body in FILES.items():
    path = os.path.join(MODELS_DIR, fname)
    with open(path, "w") as f:
        f.write(COMMON_IMPORTS + "\n\n" + dedent(body).strip() + "\n")
    print(f"✔ created {fname}")

# Write __init__.py
init_path = os.path.join(MODELS_DIR, "__init__.py")
with open(init_path, "w") as f:
    for fname in FILES:
        mod = fname.replace(".py", "")
        f.write(f"from .{mod} import *\n")

print("\n🎉 db/models split completed.")

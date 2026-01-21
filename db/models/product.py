from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    sku = Column(String, unique=True, nullable=False)
    stock_quantity = Column(Integer, default=0)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    # =========================
    # RELATIONSHIPS
    # =========================

    category = relationship(
        "Category",
        back_populates="products",
    )

    seller = relationship(
        "Seller",
        back_populates="products",
    )

    cart_items = relationship(
        "CartItem",
        back_populates="product",
        cascade="all, delete-orphan",
    )

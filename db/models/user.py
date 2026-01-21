from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


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

    # OPTIONAL (frontend depends on this)
    phone_number = Column(String, unique=True, nullable=True)

    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # =========================
    # RELATIONSHIPS
    # =========================

    # One User → One Seller (only if role = SELLER)
    seller = relationship(
        "Seller",
        back_populates="user",
        uselist=False,
    )

    # One User → Many CartItems
    cart_items = relationship(
        "CartItem",
        back_populates="user",
        cascade="all, delete-orphan",
    )

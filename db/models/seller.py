from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)

    # FK to users table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Business info
    store_name = Column(String, nullable=False)
    store_description = Column(Text, nullable=True)
    store_address = Column(Text, nullable=True)
    business_license = Column(String, nullable=True)

    gst_number = Column(String, nullable=True)
    bank_account_number = Column(String, nullable=True)
    bank_ifsc_code = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)

    # =========================
    # RELATIONSHIPS
    # =========================

    # One Seller → One User
    user = relationship(
        "User",
        back_populates="seller",
        lazy="joined",
    )

    # One Seller → Many Products
    products = relationship(
        "Product",
        back_populates="seller",
        cascade="all, delete-orphan",
    )

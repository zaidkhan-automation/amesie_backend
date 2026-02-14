from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from core.database import Base


class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    store_name = Column(String, nullable=False)
    store_description = Column(Text, nullable=True)
    store_address = Column(Text, nullable=True)

    gst_number = Column(String, nullable=True)
    bank_account_number = Column(String, nullable=True)
    bank_ifsc_code = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)
    rating = Column(Float, nullable=True, default=None)

    user = relationship("User", back_populates="seller")
    products = relationship("Product", back_populates="seller")

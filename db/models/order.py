# db/models/order.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)

    total_amount = Column(Float, nullable=False)

    # pending → confirmed → completed / cancelled
    order_status = Column(String, default="pending")

    payment_id = Column(String, nullable=True, index=True)
    payment_status = Column(String, default="pending")

    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
    order_items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

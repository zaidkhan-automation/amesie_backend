from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True, nullable=False)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    clicked = Column(Boolean, default=False)
    added_to_cart = Column(Boolean, default=False)
    purchased = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())

    product = relationship("Product")

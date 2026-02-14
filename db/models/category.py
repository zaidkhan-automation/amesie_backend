# db/models/category.py

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from core.database import Base

class Category(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    products = relationship(
        "Product",
        back_populates="category",
        lazy="selectin",
    )

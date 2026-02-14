from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from core.database import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    label = Column(String)
    street_address = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String)
    postal_code = Column(String)
    latitude = Column(String)
    longitude = Column(String)
    is_primary = Column(Boolean, default=False)
    is_temporary = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

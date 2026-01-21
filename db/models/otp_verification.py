from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from core.database import Base

class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, index=True, nullable=False)
    otp_hash = Column(String, nullable=False)
    purpose = Column(String, nullable=False, default="auth")

    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)

    verified = Column(Boolean, default=False)
    used = Column(Boolean, default=False)

    payload = Column(JSON, nullable=True)  # 🔥 pending registration data

    last_sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

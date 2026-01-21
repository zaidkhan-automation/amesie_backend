# services/otp_service.py

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
from db import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

OTP_EXPIRY_MINUTES = 10
MAX_ATTEMPTS = 5


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


def hash_otp(otp: str) -> str:
    # ✅ bcrypt ONLY (NO sha256 anywhere)
    return pwd_context.hash(otp)


def verify_otp(
    *,
    db: Session,
    email: str,
    otp: str,
    purpose: str,
):
    otp_row = (
        db.query(models.OTPVerification)
        .filter(
            models.OTPVerification.email == email,
            models.OTPVerification.purpose == purpose,
            models.OTPVerification.verified.is_(False),
        )
        .order_by(models.OTPVerification.created_at.desc())
        .with_for_update()
        .first()
    )

    if not otp_row:
        raise HTTPException(status_code=400, detail="OTP not found or already used")

    if otp_row.attempts is None:
        otp_row.attempts = 0

    if otp_row.attempts >= MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many OTP attempts")

    if otp_row.expires_at < datetime.utcnow():
        otp_row.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired")

    if not pwd_context.verify(otp, otp_row.otp_hash):
        otp_row.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # ✅ SUCCESS
    otp_row.verified = True
    otp_row.attempts += 1
    db.commit()

    return True


def otp_expiry_time():
    return datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from core.database import get_db
from db import models
from db.models import OTPVerification

from schemas.auth import UserRegisterRequest, SellerRegisterRequest, LoginRequest
from schemas.otp import OTPVerifyRequest
from schemas import schemas

from services.otp_service import generate_otp, hash_otp, otp_expiry_time
from services.email_service import send_otp_email
from services.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter()
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─────────────────────────────
# BUYER REGISTER (NO ROLE INPUT)
# ─────────────────────────────
@router.post("/register")
def register_user(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")

    now = datetime.utcnow()

    otp = generate_otp()
    otp_row = OTPVerification(
        email=payload.email,
        otp_hash=hash_otp(otp),
        purpose="auth",
        expires_at=otp_expiry_time(),
        payload={
            "type": "USER",
            "data": payload.dict(),
        },
        last_sent_at=now,
    )

    db.add(otp_row)
    db.commit()

    send_otp_email(payload.email, otp)
    return {"detail": "OTP sent. Please verify to complete registration."}


# ─────────────────────────────
# SELLER REGISTER (UNCHANGED)
# ─────────────────────────────
@router.post("/register/seller")
def register_seller(
    payload: SellerRegisterRequest,
    db: Session = Depends(get_db),
):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")

    now = datetime.utcnow()
    otp = generate_otp()

    otp_row = OTPVerification(
        email=payload.email,
        otp_hash=hash_otp(otp),
        purpose="auth",
        expires_at=otp_expiry_time(),
        payload={
            "type": "SELLER",
            "data": payload.dict(),
        },
        last_sent_at=now,
    )

    db.add(otp_row)
    db.commit()

    send_otp_email(payload.email, otp)
    return {"detail": "OTP sent. Please verify to complete seller registration."}


# ─────────────────────────────
# OTP VERIFY (ROLE HARD ENFORCED)
# ─────────────────────────────
@router.post("/verify-otp")
def verify_otp_endpoint(
    payload: OTPVerifyRequest,
    db: Session = Depends(get_db),
):
    otp_row = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.email == payload.email,
            OTPVerification.used.is_(False),
        )
        .order_by(OTPVerification.created_at.desc())
        .with_for_update()
        .first()
    )

    if not otp_row or not pwd_context.verify(payload.otp, otp_row.otp_hash):
        raise HTTPException(400, "Invalid or expired OTP")

    if datetime.utcnow() > otp_row.expires_at:
        raise HTTPException(400, "OTP expired")

    data = otp_row.payload

    try:
        if data["type"] == "USER":
            d = data["data"]
            user = models.User(
                email=d["email"],
                hashed_password=get_password_hash(d["password"]),
                full_name=d["full_name"],
                phone_number=d.get("phone_number"),
                role=models.UserRole.CUSTOMER,  # 🔒 LOCKED
                is_active=True,
            )
            db.add(user)
            db.flush()

        elif data["type"] == "SELLER":
            d = data["data"]
            user = models.User(
                email=d["email"],
                hashed_password=get_password_hash(d["password"]),
                full_name=d["full_name"],
                phone_number=d.get("phone_number"),
                role=models.UserRole.SELLER,
                is_active=True,
            )
            db.add(user)
            db.flush()

            seller = models.Seller(
                user_id=user.id,
                store_name=d["store_name"],
                store_description=d.get("store_description"),
                store_address=d.get("store_address"),
                gst_number=d.get("gst_number"),
                bank_account_number=d.get("bank_account_number"),
                bank_ifsc_code=d.get("bank_ifsc_code"),
                is_active=True,
                is_verified=True,
            )
            db.add(seller)

        otp_row.used = True
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "User already registered")

    except Exception:
        db.rollback()
        raise HTTPException(500, "Registration failed")

    return {"message": "Registration completed successfully"}


# ─────────────────────────────
# LOGIN (UNCHANGED)
# ─────────────────────────────
@router.post("/login", response_model=schemas.Token)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(payload.email, payload.password, db)
    if not user:
        raise HTTPException(401, "Incorrect email or password")

    token_data = {"sub": user.email, "role": user.role.value}

    if user.role == models.UserRole.SELLER:
        seller = db.query(models.Seller).filter(models.Seller.user_id == user.id).first()
        if seller:
            token_data["seller_id"] = seller.id

    token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from db import models
from db.models import OTPVerification

from schemas.auth import SellerRegisterRequest, LoginRequest
from schemas.otp import OTPVerifyRequest
from schemas import schemas

from services.otp_service import (
    generate_otp,
    hash_otp,
    otp_expiry_time,
    verify_otp,
)
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

# =====================================================
# REGISTER USER → SEND OTP ONLY
# =====================================================

@router.post("/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(400, "Email already registered")

    now = datetime.utcnow()

    otp_row = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.email == user.email,
            OTPVerification.used.is_(False),
        )
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

    if otp_row and otp_row.expires_at > now:
        raise HTTPException(202, "OTP already sent. Please check email.")

    otp = generate_otp()

    otp_row = OTPVerification(
        email=user.email,
        otp_hash=hash_otp(otp),
        purpose="auth",
        expires_at=otp_expiry_time(),
        payload={
            "type": "USER",
            "data": user.dict(),
        },
        last_sent_at=now,
    )

    db.add(otp_row)
    db.commit()

    try:
        send_otp_email(user.email, otp)
    except Exception as e:
        logger.error(f"Email failed: {e}")
        raise HTTPException(400, "Email not reachable or invalid")

    return {"detail": "OTP sent. Please verify to complete registration."}

# =====================================================
# REGISTER SELLER → SEND OTP ONLY
# =====================================================

@router.post("/register/seller")
def register_seller(payload: SellerRegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")

    now = datetime.utcnow()

    otp_row = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.email == payload.email,
            OTPVerification.used.is_(False),
        )
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

    if otp_row and otp_row.expires_at > now:
        raise HTTPException(202, "OTP already sent. Please check email.")

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

    try:
        send_otp_email(payload.email, otp)
    except Exception as e:
        logger.error(f"Email failed: {e}")
        raise HTTPException(400, "Email not reachable or invalid")

    return {"detail": "OTP sent. Please verify to complete seller registration."}

# =====================================================
# VERIFY OTP → FINALIZE REGISTRATION
# =====================================================

@router.post("/verify-otp")
def verify_otp_endpoint(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
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

    if not otp_row:
        raise HTTPException(400, "Invalid or expired OTP")

    verify_otp(
        db=db,
        email=payload.email,
        otp=payload.otp,
        purpose=payload.purpose,
    )

    data = otp_row.payload
    if not data:
        raise HTTPException(500, "Registration payload missing")

    if data["type"] == "USER":
        d = data["data"]
        user = models.User(
            email=d["email"],
            hashed_password=get_password_hash(d["password"]),
            full_name=d["full_name"],
            phone_number=d["phone_number"],
            role=models.UserRole.CUSTOMER,
            is_active=True,
        )
        db.add(user)

    elif data["type"] == "SELLER":
        d = data["data"]
        user = models.User(
            email=d["email"],
            hashed_password=get_password_hash(d["password"]),
            full_name=d["full_name"],
            phone_number=d["phone_number"],
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

    return {"message": "Registration completed successfully"}

# =====================================================
# LOGIN
# =====================================================

@router.post("/login", response_model=schemas.Token)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(payload.email, payload.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token_data = {
        "sub": user.email,
        "role": user.role.value,
    }

    if user.role == models.UserRole.SELLER:
        seller = (
            db.query(models.Seller)
            .filter(models.Seller.user_id == user.id)
            .first()
        )
        if seller:
            token_data["seller_id"] = seller.id

    token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": token, "token_type": "bearer"}

# =====================================================
# ME
# =====================================================

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

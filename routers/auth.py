from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter()

# -------------------------
# USER REGISTER
# -------------------------
@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(400, "Email already registered")

    db_user = models.User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        phone_number=user.phone_number,
        role=models.UserRole.CUSTOMER,
        is_active=True,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# -------------------------
# SELLER REGISTER (AUTO APPROVED ✅)
# -------------------------
@router.post("/register/seller")
def register_seller(
    full_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    store_name: str = Form(...),
    store_description: str = Form(None),
    store_address: str = Form(...),
    business_license: str = Form(None),
    gst_number: str = Form(None),
    bank_account_number: str = Form(None),
    bank_ifsc_code: str = Form(None),
    db: Session = Depends(get_db),
):
    # Check existing user
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(400, "Email already registered")

    # 1️⃣ Create USER
    user = models.User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        phone_number=phone_number,
        role=models.UserRole.SELLER,
        is_active=True,
    )
    db.add(user)
    db.flush()  # ensures user.id is available

    # 2️⃣ Create SELLER (AUTO APPROVED)
    seller = models.Seller(
        user_id=user.id,
        store_name=store_name,
        store_description=store_description,
        store_address=store_address,
        business_license=business_license,
        gst_number=gst_number,
        bank_account_number=bank_account_number,
        bank_ifsc_code=bank_ifsc_code,

        # 🔥 REAL AUTO APPROVAL (matches DB trigger)
        is_verified=True,
        is_active=True,
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    return {
        "message": "Seller registered and auto-approved",
        "seller_id": seller.id,
    }


# -------------------------
# ADMIN REGISTER
# -------------------------
@router.post("/register/admin", response_model=schemas.User)
def register_admin(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(400, "Email already registered")

    db_user = models.User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        phone_number=user.phone_number,
        role=models.UserRole.ADMIN,
        is_active=True,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# -------------------------
# LOGIN
# -------------------------
@router.post("/login", response_model=schemas.Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": token, "token_type": "bearer"}


# -------------------------
# ME
# -------------------------
@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db
from db import models
from schemas import schemas
from services.auth import authenticate_user, create_access_token, get_password_hash, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from core.logging_config import get_logger

router = APIRouter()
auth_logger = get_logger('auth')

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    auth_logger.info(f"New user registration attempt: {user.email}")
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        auth_logger.warning(f"Registration failed - email already exists: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user with CUSTOMER role by default
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone_number,
        role=models.UserRole.CUSTOMER
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    auth_logger.info(f"User registered successfully: {user.email}")
    return db_user

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
    db: Session = Depends(get_db)
):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new seller user
    hashed_password = get_password_hash(password)
    db_user = models.User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        phone_number=phone_number,
        role=models.UserRole.SELLER
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create seller profile
    db_seller = models.Seller(
        user_id=db_user.id,
        store_name=store_name,
        store_description=store_description,
        store_logo_url=None,  # Can be added later via profile update
        business_license=business_license,
        gst_number=gst_number,
        bank_account_number=bank_account_number,
        bank_ifsc_code=bank_ifsc_code,
        store_address=store_address
    )
    
    db.add(db_seller)
    db.commit()
    
    return {"message": "Seller registered successfully", "user_id": db_user.id}

@router.post("/register/admin", response_model=schemas.User)
def register_admin(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new admin user
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone_number,
        role=models.UserRole.ADMIN
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=schemas.Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth_logger.info(f"Login attempt for user: {form_data.username}")
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        auth_logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    auth_logger.info(f"Successful login for user: {user.email} (Role: {user.role.value})")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    auth_logger.info(f"User profile accessed: {current_user.email}")
    return current_user

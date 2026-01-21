import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.database import get_db
from db import models

# ─────────────────────────────────────────────
# SECURITY SETTINGS (SINGLE SOURCE OF TRUTH)
# ─────────────────────────────────────────────
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET not set in environment")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─────────────────────────────────────────────
# PASSWORD NORMALIZATION (bcrypt hard limit fix)
# ─────────────────────────────────────────────
def _normalize_password(password: str) -> str:
    """
    bcrypt supports max 72 BYTES.
    This avoids silent verification failures.
    """
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")

def get_password_hash(password: str) -> str:
    password = _normalize_password(password)
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = _normalize_password(plain_password)
    return pwd_context.verify(plain_password, hashed_password)

# ─────────────────────────────────────────────
# JWT CREATION
# ─────────────────────────────────────────────
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
):
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        JWT_SECRET,
        algorithm=ALGORITHM,
    )

# ─────────────────────────────────────────────
# JWT VERIFICATION (HTTP)
# ─────────────────────────────────────────────
def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM],
        )
        email: str | None = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        return email

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ─────────────────────────────────────────────
# CURRENT USER (HTTP)
# ─────────────────────────────────────────────
def get_current_user(
    email: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

# ─────────────────────────────────────────────
# LOGIN AUTH
# ─────────────────────────────────────────────
def authenticate_user(
    email: str,
    password: str,
    db: Session,
):
    user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user

# ─────────────────────────────────────────────
# RAW JWT DECODE (WebSocket / Agent)
# ─────────────────────────────────────────────
def decode_token_raw(token: str) -> dict:
    """
    Decode JWT without FastAPI Depends.
    Used by WebSocket / agent auth.
    """
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

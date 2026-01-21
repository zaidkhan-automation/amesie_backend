# core/auth.py
import jwt
from datetime import datetime, timedelta

JWT_SECRET = "SUPER_SECRET_CHANGE_THIS"
JWT_ALGORITHM = "HS256"
JWT_EXP_MINUTES = 60 * 24


def create_access_token(payload: dict):
    data = payload.copy()
    data["exp"] = datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

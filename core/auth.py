# core/auth.py
import jwt
from datetime import datetime, timedelta

JWT_EXP_MINUTES = 60 * 24


JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"

def create_token(data: dict):
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)
def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

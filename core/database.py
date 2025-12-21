import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Load env
# ─────────────────────────────────────────────
load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    raise RuntimeError("❌ Missing required Postgres environment variables")

# ─────────────────────────────────────────────
# DATABASE URL
# ⚠️ IMPORTANT:
# - Use plain `postgresql://`
# - NOT `postgresql+psycopg2://`
# (SQLAlchemy will auto-pick psycopg2)
# ─────────────────────────────────────────────
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:"
    f"{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:"
    f"{POSTGRES_PORT}/"
    f"{POSTGRES_DB}"
)

# ─────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    echo=False,           # 🔥 PROD: False (enable only while debugging)
    pool_pre_ping=True,   # 🔥 Avoid stale connections
    future=True
)

# ─────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)

# ─────────────────────────────────────────────
# Base
# ─────────────────────────────────────────────
Base = declarative_base()

# ─────────────────────────────────────────────
# FastAPI dependency
# ─────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Load .env once
# ─────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────
# Resolve DATABASE_URL safely
# ─────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")  # SAFE DEFAULT
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB")

    if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
        raise RuntimeError("❌ Missing Postgres environment variables")

    DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:"
        f"{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:"
        f"{POSTGRES_PORT}/"
        f"{POSTGRES_DB}"
    )

# ─────────────────────────────────────────────
# Engine (DO NOT CONNECT YET)
# ─────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

# ─────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

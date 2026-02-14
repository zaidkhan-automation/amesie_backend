# routers/categories.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from db import models

router = APIRouter()

@router.get("/")
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

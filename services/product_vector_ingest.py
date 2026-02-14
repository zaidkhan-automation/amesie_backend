from sqlalchemy.orm import Session
from db import models
from services.vector_service import upsert_product_vector


def index_product(db: Session, product_id: int):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )

    if not product:
        return

    upsert_product_vector(product)

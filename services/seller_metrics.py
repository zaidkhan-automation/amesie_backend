from sqlalchemy.orm import Session
from sqlalchemy import func
from db import models

LOW_STOCK_THRESHOLD = 5


def get_seller_metrics(db: Session, seller_id: int) -> dict:
    # -------------------------
    # PRODUCT METRICS
    # -------------------------
    products = (
        db.query(models.Product)
        .filter(
            models.Product.seller_id == seller_id,
            models.Product.is_deleted.is_(False),
        )
        .all()
    )

    total_products = len(products)
    active_products = sum(1 for p in products if p.is_active)
    inactive_products = total_products - active_products
    out_of_stock = sum(1 for p in products if (p.stock_quantity or 0) == 0)
    low_stock = sum(
        1 for p in products
        if 0 < (p.stock_quantity or 0) <= LOW_STOCK_THRESHOLD
    )

    # -------------------------
    # ORDER METRICS (FIXED)
    # -------------------------
    orders_today = (
        db.query(func.count(func.distinct(models.OrderItem.order_id)))
        .join(models.Product, models.Product.id == models.OrderItem.product_id)
        .join(models.Order, models.Order.id == models.OrderItem.order_id)
        .filter(
            models.Product.seller_id == seller_id,
            func.date(models.Order.created_at) == func.current_date(),
        )
        .scalar()
    ) or 0

    revenue_today = (
        db.query(
            func.coalesce(
                func.sum(models.OrderItem.quantity * models.OrderItem.price), 0
            )
        )
        .join(models.Product, models.Product.id == models.OrderItem.product_id)
        .join(models.Order, models.Order.id == models.OrderItem.order_id)
        .filter(
            models.Product.seller_id == seller_id,
            func.date(models.Order.created_at) == func.current_date(),
        )
        .scalar()
    ) or 0

    return {
        "total_products": total_products,
        "active_products": active_products,
        "inactive_products": inactive_products,
        "out_of_stock": out_of_stock,
        "low_stock": low_stock,
        "orders_today": orders_today,
        "revenue_today": float(revenue_today),
    }

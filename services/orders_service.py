from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from services.notification_service import (
    notify_order_created,
    notify_seller_new_order,
    notify_payment_success,
)

# ─────────────────────────────────────────────
# CREATE ORDER (NO COMMIT HERE)
# ─────────────────────────────────────────────
def create_order_db(
    db: Session,
    user_id: int,
    location_id: int,
    total: float,
) -> int:
    """
    Creates order using DB stored procedure.
    Returns order_id.
    """
    result = db.execute(
        text("SELECT create_order(:uid, :loc, :total)"),
        {
            "uid": user_id,
            "loc": location_id,
            "total": total,
        },
    )

    order_id = result.scalar()
    if not order_id:
        raise HTTPException(status_code=500, detail="Order creation failed")

    # 🔔 Buyer notification
    notify_order_created(
        db=db,
        user_id=user_id,
        order_id=order_id,
    )

    return order_id


# ─────────────────────────────────────────────
# ADD ORDER ITEM (DB HANDLES STOCK + LOCKS)
# ─────────────────────────────────────────────
def add_order_item_db(
    db: Session,
    order_id: int,
    user_id: int,
    product_id: int,
    quantity: int,
) -> None:
    """
    Adds item to order.
    Stock validation + locking is enforced in DB.
    """
    db.execute(
        text("SELECT add_order_item(:oid, :uid, :pid, :qty)"),
        {
            "oid": order_id,
            "uid": user_id,
            "pid": product_id,
            "qty": quantity,
        },
    )

    # 🔔 Seller notification (per product)
    seller_row = db.execute(
        text("""
            SELECT s.user_id
            FROM products p
            JOIN sellers s ON s.id = p.seller_id
            WHERE p.id = :pid
        """),
        {"pid": product_id},
    ).fetchone()

    if seller_row:
        notify_seller_new_order(
            db=db,
            seller_user_id=seller_row.user_id,
            order_id=order_id,
        )


# ─────────────────────────────────────────────
# MARK PAYMENT SUCCESS (LOCK ORDER IN DB)
# ─────────────────────────────────────────────
def mark_payment_success_db(
    db: Session,
    order_id: int,
    payment_id: str,
    method: str,
) -> None:
    """
    Marks order as paid.
    DB procedure locks order & updates state atomically.
    """
    db.execute(
        text("SELECT mark_payment_success(:oid, :pid, :method)"),
        {
            "oid": order_id,
            "pid": payment_id,
            "method": method,
        },
    )

    # 🔔 Buyer notification
    order_user = db.execute(
        text("SELECT user_id FROM orders WHERE id = :oid"),
        {"oid": order_id},
    ).fetchone()

    if order_user:
        notify_payment_success(
            db=db,
            user_id=order_user.user_id,
            order_id=order_id,
        )

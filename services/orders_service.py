from sqlalchemy.orm import Session
from sqlalchemy import text


def create_order_db(
    db: Session,
    user_id: int,
    location_id: int,
    total: float
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
            "total": total
        }
    )
    order_id = result.scalar()
    db.commit()
    return order_id


def add_order_item_db(
    db: Session,
    order_id: int,
    user_id: int,
    product_id: int,
    quantity: int
) -> None:
    """
    Adds item to order (stock handled in DB).
    """
    try:
        db.execute(
            text("SELECT add_order_item(:oid, :uid, :pid, :qty)"),
            {
                "oid": order_id,
                "uid": user_id,
                "pid": product_id,
                "qty": quantity
            }
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


def mark_payment_success_db(
    db: Session,
    order_id: int,
    payment_id: str,
    method: str
) -> None:
    """
    Marks order as paid.
    Locks order & emits events in DB.
    """
    try:
        db.execute(
            text("SELECT mark_payment_success(:oid, :pid, :method)"),
            {
                "oid": order_id,
                "pid": payment_id,
                "method": method
            }
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

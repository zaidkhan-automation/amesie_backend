import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CREATE ORDER
# ─────────────────────────────────────────────
def create_order_db(
    db: Session,
    user_id: int,
    location_id: int,
    total: float,
) -> int:
    """
    Creates order using DB stored procedure.
    DB is responsible for:
    - order row
    - order_items
    - stock locking & decrement
    """
    try:
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
            logger.error(
                f"create_order returned NULL for user_id={user_id}"
            )
            raise HTTPException(500, "Order creation failed")

        return order_id

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            f"DB error in create_order_db for user_id={user_id}"
        )
        raise HTTPException(500, "Order creation failed")


# ─────────────────────────────────────────────
# PAYMENT SUCCESS (DB ONLY)
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
    try:
        db.execute(
            text("SELECT mark_payment_success(:oid, :pid, :method)"),
            {
                "oid": order_id,
                "pid": payment_id,
                "method": method,
            },
        )

    except Exception:
        logger.exception(
            f"Failed to mark payment success for order_id={order_id}"
        )
        raise HTTPException(500, "Failed to mark payment success")

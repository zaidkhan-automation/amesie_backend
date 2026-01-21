# db/models/user_facts.py

import uuid
from sqlalchemy import text
from core.database import SessionLocal


def get_fact_by_key_value(
    *,
    user_id: str,
    fact_key: str,
    fact_value: str,
) -> dict | None:
    """
    Returns:
    {
        fact_id: str,
        r_raw: float,
        p_raw: float
    }
    """

    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT
                    fact_id,
                    r_raw,
                    p_raw
                FROM user_facts
                WHERE
                    user_id = :user_id
                    AND fact_key = :fact_key
                    AND fact_value = :fact_value
                    AND active = TRUE
                LIMIT 1
            """),
            {
                "user_id": user_id,
                "fact_key": fact_key,
                "fact_value": fact_value,
            },
        ).fetchone()

        if not result:
            return None

        return {
            "fact_id": result.fact_id,
            "r_raw": float(result.r_raw),
            "p_raw": float(result.p_raw),
        }

    finally:
        db.close()


def increment_reinforcement(
    *,
    user_id: str,
    fact_key: str,
    fact_value: str,
    amount: float = 1.0,
):
    """
    Explicit confirmation → reinforcement increases slowly
    """
    db = SessionLocal()
    try:
        db.execute(
            text("""
                UPDATE user_facts
                SET
                    r_raw = r_raw + :amount,
                    last_confirmed_at = NOW()
                WHERE
                    user_id = :user_id
                    AND fact_key = :fact_key
                    AND fact_value = :fact_value
                    AND active = TRUE
            """),
            {
                "user_id": user_id,
                "fact_key": fact_key,
                "fact_value": fact_value,
                "amount": amount,
            },
        )
        db.commit()
    finally:
        db.close()


def increment_contradiction(
    *,
    user_id: str,
    fact_key: str,
    fact_value: str,
    amount: float = 1.5,  # ⚠️ penalty grows faster
):
    """
    Explicit negation → penalty increases faster than reinforcement
    """
    db = SessionLocal()
    try:
        db.execute(
            text("""
                UPDATE user_facts
                SET
                    p_raw = p_raw + :amount
                WHERE
                    user_id = :user_id
                    AND fact_key = :fact_key
                    AND fact_value = :fact_value
                    AND active = TRUE
            """),
            {
                "user_id": user_id,
                "fact_key": fact_key,
                "fact_value": fact_value,
                "amount": amount,
            },
        )
        db.commit()
    finally:
        db.close()


def insert_user_fact(
    *,
    user_id: str,
    chat_id: str,
    fact_key: str,
    fact_value: str,
    confidence: float,
    source: str = "llm_extraction",
):
    """
    Inserts a user fact and returns fact_id
    """

    fact_id = str(uuid.uuid4())

    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO user_facts (
                    fact_id,
                    user_id,
                    fact_key,
                    fact_value,
                    r_raw,
                    p_raw,
                    source,
                    active
                )
                VALUES (
                    :fact_id,
                    :user_id,
                    :fact_key,
                    :fact_value,
                    :r_raw,
                    0.0,
                    :source,
                    TRUE
                )
            """),
            {
                "fact_id": fact_id,
                "user_id": user_id,
                "fact_key": fact_key,
                "fact_value": fact_value,
                "r_raw": float(confidence),
                "source": source,
            },
        )
        db.commit()
        return fact_id

    finally:
        db.close()

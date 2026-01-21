# services/fact_reinforce.py

from db.models.user_facts import (
    increment_reinforcement,
    increment_contradiction,
    get_fact_by_key_value,   # 🔹 must return fact_id, r_raw, p_raw
)

from vectorstore.qdrant_writer import update_user_fact_payload


def reinforce_fact(
    *,
    user_id: str,
    fact_key: str,
    fact_value: str,
):
    """
    Explicit user confirmation of a fact.
    Increases reinforcement and syncs Qdrant payload.
    """

    # 1️⃣ Update DB (source of truth)
    increment_reinforcement(
        user_id=user_id,
        fact_key=fact_key,
        fact_value=fact_value,
    )

    # 2️⃣ Read updated state
    fact = get_fact_by_key_value(
        user_id=user_id,
        fact_key=fact_key,
        fact_value=fact_value,
    )

    if not fact:
        return

    # 3️⃣ Sync Qdrant payload
    update_user_fact_payload(
        fact_id=fact["fact_id"],
        r_raw=fact["r_raw"],
        p_raw=fact["p_raw"],
    )


def contradict_fact(
    *,
    user_id: str,
    fact_key: str,
    fact_value: str,
):
    """
    Explicit user contradiction of a fact.
    Increases contradiction and syncs Qdrant payload.
    """

    # 1️⃣ Update DB
    increment_contradiction(
        user_id=user_id,
        fact_key=fact_key,
        fact_value=fact_value,
    )

    # 2️⃣ Read updated state
    fact = get_fact_by_key_value(
        user_id=user_id,
        fact_key=fact_key,
        fact_value=fact_value,
    )

    if not fact:
        return

    # 3️⃣ Sync Qdrant payload
    update_user_fact_payload(
        fact_id=fact["fact_id"],
        r_raw=fact["r_raw"],
        p_raw=fact["p_raw"],
    )

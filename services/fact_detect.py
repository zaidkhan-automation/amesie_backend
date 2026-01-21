# services/fact_detect.py

from typing import Literal, Optional

from services.fact_reinforce import reinforce_fact, contradict_fact


def detect_fact_confirmation(
    *,
    user_id: str,
    message: str,
    fact_key: str,
    fact_value: str,
) -> Optional[Literal["reinforce", "contradict"]]:
    """
    Very strict explicit detection.
    No inference. No guessing.
    """

    msg = message.lower().strip()
    val = fact_value.lower()

    # Explicit confirmation patterns
    confirm_phrases = [
        f"my {fact_key} is {val}",
        f"yes my {fact_key} is {val}",
        f"correct my {fact_key} is {val}",
        f"that's right my {fact_key} is {val}",
    ]

    # Explicit contradiction patterns
    contradict_phrases = [
        f"no my {fact_key} is not {val}",
        f"my {fact_key} is not {val}",
        f"that's wrong my {fact_key} is not {val}",
    ]

    if any(p in msg for p in confirm_phrases):
        reinforce_fact(
            user_id=user_id,
            fact_key=fact_key,
            fact_value=fact_value,
        )
        return "reinforce"

    if any(p in msg for p in contradict_phrases):
        contradict_fact(
            user_id=user_id,
            fact_key=fact_key,
            fact_value=fact_value,
        )
        return "contradict"

    return None

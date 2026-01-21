# llm/context_builder.py

from typing import List


def build_llm_prompt(
    *,
    retrieved_context: List[str],
    user_message: str,
) -> str:
    """
    Hard-bounded prompt.
    Prevents LLM from replying to old turns.
    """

    context_block = ""
    if retrieved_context:
        context_block = (
            "PAST CONVERSATION (for context only):\n"
            + "\n".join(f"- {c}" for c in retrieved_context)
            + "\n\n"
        )

    prompt = (
        context_block
        + "CURRENT USER MESSAGE:\n"
        + user_message
    )

    return prompt

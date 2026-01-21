RAW_TURNS_TO_KEEP = 4
CONTEXT_TOKEN_LIMIT = 1500


def build_context_prompt(
    *,
    chat_id: str,
    recent_threads: list,
    tokenizer,
    latest_summary=None,
    max_turns: int = 6,
    max_tokens: int = 1500,
):
    """
    Build conversation context for prompt injection.

    Supports:
    - tokenizer(text) -> list[int]
    - tokenizer.encode(text) -> list[int]

    Supports recent_threads as:
    - dict: {"user": str, "assistant": str}
    - tuple: (user_text, assistant_text)
    """

    # ─── TOKENIZER NORMALIZATION ─────────────
    if callable(tokenizer):
        def count_tokens(text: str) -> int:
            return len(tokenizer(text))
    elif hasattr(tokenizer, "encode"):
        def count_tokens(text: str) -> int:
            return len(tokenizer.encode(text))
    else:
        raise TypeError("tokenizer must be callable or have .encode()")

    # ─── SAFE ACCESSORS ──────────────────────
    def get_user(turn):
        if isinstance(turn, dict):
            return turn.get("user")
        if isinstance(turn, (list, tuple)):
            return turn[0]
        raise TypeError("Invalid turn format")

    def get_assistant(turn):
        if isinstance(turn, dict):
            return turn.get("assistant")
        if isinstance(turn, (list, tuple)):
            return turn[1]
        raise TypeError("Invalid turn format")

    def get_attr(obj, key):
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    parts = []
    token_count = 0

    def add(text: str) -> bool:
        nonlocal token_count
        tokens = count_tokens(text)
        if token_count + tokens > max_tokens:
            return False
        parts.append(text)
        token_count += tokens
        return True

    # ─── SUMMARY FIRST (IF EXISTS) ───────────
    if latest_summary:
        summary_block = (
            "[Conversation Summary]\n"
            f"User: {get_attr(latest_summary, 'user_summary')}\n"
            f"Assistant: {get_attr(latest_summary, 'assistant_summary')}\n"
        )
        add(summary_block)

    # ─── RECENT RAW TURNS ────────────────────
    for turn in reversed(recent_threads[-max_turns:]):
        block = (
            f"User: {get_user(turn)}\n"
            f"Assistant: {get_assistant(turn)}\n"
        )
        if not add(block):
            break

    parts.append("[Continue the conversation naturally]")

    return "\n".join(parts)

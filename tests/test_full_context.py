from core.database import SessionLocal
from memory.context_loader import load_conversation_context
from memory.context_builder import build_context_prompt


def test_full_context_and_token_limit():
    db = SessionLocal()

    # ─────────────────────────────────────────
    # TEST 3: REAL DB CONTEXT BUILD
    # ─────────────────────────────────────────
    threads, summary = load_conversation_context(db, "seller_16_chat_1")

    context = build_context_prompt(
        chat_id="seller_16_chat_1",
        recent_threads=[
            {"user": t["user_raw_text"], "assistant": t["assistant_raw_text"]}
            for t in threads
        ],
        latest_summary=summary,
        tokenizer=lambda x: x.split(),  # simple tokenizer for test
    )

    print("\n===== TEST 3: FULL CONTEXT =====")
    print(context)
    print("================================\n")

    assert "[Conversation Summary]" in context
    assert "[Continue the conversation naturally]" in context

    # ─────────────────────────────────────────
    # TEST 4: TOKEN LIMIT SAFETY
    # ─────────────────────────────────────────
    long_text = "hello " * 2000  # ~2000 tokens

    context_limited = build_context_prompt(
        chat_id="overflow_test",
        recent_threads=[
            {"user": long_text, "assistant": long_text},
            {"user": long_text, "assistant": long_text},
        ],
        latest_summary={
            "user_summary": "User talked a lot",
            "assistant_summary": "Assistant replied briefly",
        },
        tokenizer=lambda x: x.split(),
        max_tokens=1500,
    )

    token_count = len(context_limited.split())

    print("===== TEST 4: TOKEN SAFETY =====")
    print("TOKENS:", token_count)
    print(context_limited)
    print("================================")

    assert token_count <= 1500
    assert "User talked a lot" in context_limited

    db.close()


if __name__ == "__main__":
    test_full_context_and_token_limit()

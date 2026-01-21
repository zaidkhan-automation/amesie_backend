# memory/context_loader.py

from sqlalchemy import text
import re


def load_conversation_context(db, chat_id: str):
    threads = db.execute(
        text("""
            SELECT user_raw_text, assistant_raw_text
            FROM conversation_threads
            WHERE chat_id = :chat_id
            ORDER BY timestamp ASC
        """),
        {"chat_id": chat_id},
    ).mappings().all()

    summary = db.execute(
        text("""
            SELECT user_summary, assistant_summary
            FROM conversation_summaries
            WHERE conversation_id = (
                SELECT id FROM conversation_threads
                WHERE chat_id = :chat_id
                ORDER BY timestamp DESC
                LIMIT 1
            )
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"chat_id": chat_id},
    ).mappings().first()

    return threads, summary


def extract_agent_hints(summary: dict):
    if not summary:
        return {}

    text_blob = (
        f"{summary.get('user_summary','')} "
        f"{summary.get('assistant_summary','')}"
    ).lower()

    hints = {}

    # ✅ NAME (STRICT: ONLY IF EXPLICIT)
    name_match = re.search(r"name is ([a-zA-Z]+)", text_blob)
    if name_match:
        hints["user_name"] = name_match.group(1)

    # ✅ FLOW
    if "create" in text_blob and "product" in text_blob:
        hints["last_flow"] = "creating_product"

    return hints

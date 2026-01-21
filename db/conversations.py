# db/conversations.py

from sqlalchemy import text
from sqlalchemy.orm import Session


def insert_thread(
    *,
    db: Session,
    chat_id: str,
    user_text: str,
    assistant_text: str,
    importance: float = 0.5,
    topic_tags=None,
):
    topic_tags = topic_tags or []

    query = text("""
        INSERT INTO conversation_threads (
            chat_id,
            user_raw_text,
            assistant_raw_text,
            importance,
            topic_tags
        )
        VALUES (
            :chat_id,
            :user_text,
            :assistant_text,
            :importance,
            :topic_tags
        )
        RETURNING id;
    """)

    result = db.execute(
        query,
        {
            "chat_id": chat_id,
            "user_text": user_text,
            "assistant_text": assistant_text,
            "importance": importance,
            "topic_tags": topic_tags,
        },
    )

    conversation_id = result.scalar()
    db.commit()
    return conversation_id


def fetch_latest_summary(db: Session, chat_id: str):
    query = text("""
        SELECT s.user_summary, s.assistant_summary
        FROM conversation_summaries s
        JOIN conversation_threads t ON t.id = s.conversation_id
        WHERE t.chat_id = :chat_id
        ORDER BY s.created_at DESC
        LIMIT 1;
    """)

    row = db.execute(query, {"chat_id": chat_id}).mappings().first()
    return row


def fetch_recent_threads(db: Session, chat_id: str, limit: int = 6):
    query = text("""
        SELECT user_raw_text, assistant_raw_text
        FROM conversation_threads
        WHERE chat_id = :chat_id
        ORDER BY timestamp DESC
        LIMIT :limit;
    """)

    rows = db.execute(
        query,
        {"chat_id": chat_id, "limit": limit},
    ).mappings().all()

    return [
        {"user": r["user_raw_text"], "assistant": r["assistant_raw_text"]}
        for r in reversed(rows)
    ]

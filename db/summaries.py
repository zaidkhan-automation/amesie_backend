# db/summaries.py

from sqlalchemy import text
from sqlalchemy.orm import Session


def insert_summary(
    *,
    db: Session,
    chat_id: str,
    user_summary: str,
    assistant_summary: str,
    summary_version: int = 1,
):
    """
    Insert a conversation summary linked to the latest conversation thread.
    """

    # Get latest conversation thread for this chat
    row = db.execute(
        text("""
            SELECT id
            FROM conversation_threads
            WHERE chat_id = :chat_id
            ORDER BY timestamp DESC
            LIMIT 1
        """),
        {"chat_id": chat_id},
    ).first()

    if not row:
        return  # nothing to summarize yet

    conversation_id = row[0]

    db.execute(
        text("""
            INSERT INTO conversation_summaries (
                conversation_id,
                user_summary,
                assistant_summary,
                summary_version
            )
            VALUES (
                :conversation_id,
                :user_summary,
                :assistant_summary,
                :summary_version
            )
        """),
        {
            "conversation_id": conversation_id,
            "user_summary": user_summary,
            "assistant_summary": assistant_summary,
            "summary_version": summary_version,
        },
    )

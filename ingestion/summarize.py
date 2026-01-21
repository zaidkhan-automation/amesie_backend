# ingestion/summarize.py

import os
import re
from mistralai import Mistral
from sqlalchemy.orm import Session

from db.conversations import fetch_recent_threads
from db.summaries import insert_summary

MODEL_NAME = "mistral-large-latest"
SUMMARY_TRIGGER_TOKENS = 200  # 🔥 EARLY TRIGGER

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])


def approx_token_count(text: str) -> int:
    return max(1, len(text) // 4)


SUMMARY_PROMPT = """
Summarize the conversation factually.
Rules:
- If the user explicitly states their name, store ONLY the latest confirmed name.
- Do NOT guess names.
- Preserve product intent and flow state.
- Be concise.

Conversation:
{conversation}
"""


def maybe_summarize_conversation(db: Session, chat_id: str) -> None:
    threads = fetch_recent_threads(db, chat_id, limit=20)
    if not threads:
        return

    convo = ""
    for t in threads:
        convo += f"User: {t['user']}\nAssistant: {t['assistant']}\n\n"

    if approx_token_count(convo) < SUMMARY_TRIGGER_TOKENS:
        return

    res = client.chat.complete(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": SUMMARY_PROMPT.format(conversation=convo)}],
        temperature=0.1,
    )

    summary = res.choices[0].message.content.strip()
    if not summary:
        return

    insert_summary(
        db=db,
        chat_id=chat_id,
        user_summary="User interaction summary",
        assistant_summary=summary,
    )
def force_summarize_conversation(
    db: Session,
    chat_id: str,
    user_note: str,
    assistant_note: str,
):
    insert_summary(
        db=db,
        chat_id=chat_id,
        user_summary=user_note,
        assistant_summary=assistant_note,
    )

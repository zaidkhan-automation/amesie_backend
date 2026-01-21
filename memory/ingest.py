# memory/ingest.py

from utils.token_counter import count_tokens
from memory.summarizer import summarize_conversation

TOKEN_LIMIT = 3000

def maybe_summarize_and_store(
    *,
    conversation_id: str,
    user_text: str,
    assistant_text: str,
    tokenizer,
    llm_client,
    db,
):
    total_tokens = (
        count_tokens(user_text, tokenizer)
        + count_tokens(assistant_text, tokenizer)
    )

    if total_tokens < TOKEN_LIMIT:
        return  # ❌ nothing to do

    summary = summarize_conversation(
        user_text=user_text,
        assistant_text=assistant_text,
        llm_client=llm_client,
    )

    db.execute(
        """
        INSERT INTO conversation_summaries (
            conversation_id,
            user_summary,
            assistant_summary,
            summary_version
        )
        VALUES (%s, %s, %s, 1)
        """,
        (
            conversation_id,
            summary["user"],
            summary["assistant"],
        ),
    )

# memory/conversation_ingest.py

from embeddings.mpnet import embed_text
from llm.summarizer import summarize, should_summarize
from vectorstore.qdrant_writer import upsert_chat_memory


def ingest_user_message(
    *,
    chat_id: str,
    user_text: str,
):
    if should_summarize(user_text):
        text_for_embedding = summarize(user_text)
        mode = "summarized"
    else:
        text_for_embedding = user_text
        mode = "full"

    embedding = embed_text(text_for_embedding)

    upsert_chat_memory(
        chat_id=chat_id,
        text=text_for_embedding,
        embedding=embedding,
        metadata={
            "role": "user",
            "mode": mode,
        },
    )


def ingest_ai_response(
    *,
    chat_id: str,
    ai_text: str,
):
    summary = summarize(ai_text)
    embedding = embed_text(summary)

    upsert_chat_memory(
        chat_id=chat_id,
        text=summary,
        embedding=embedding,
        metadata={
            "role": "assistant",
            "mode": "summarized",
        },
    )

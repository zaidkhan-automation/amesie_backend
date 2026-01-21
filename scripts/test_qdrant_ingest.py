from memory.conversation_ingest import (
    ingest_user_message,
    ingest_ai_response,
)

CHAT_ID = "test_chat_001"

print("🧪 Ingesting user message...")
ingest_user_message(
    chat_id=CHAT_ID,
    user_text="I am planning to build an affordable shoe brand for students."
)

print("🧪 Ingesting AI response...")
ingest_ai_response(
    chat_id=CHAT_ID,
    ai_text=(
        "You want to build a student-focused shoe brand that is affordable, "
        "lightweight, and scalable over time."
    )
)

print("✅ Done. Check Qdrant.")

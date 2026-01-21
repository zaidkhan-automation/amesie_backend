from core.database import SessionLocal
from memory.context_loader import load_conversation_context

def test_loader():
    db = SessionLocal()
    threads, summary = load_conversation_context(db, "seller_16_chat_1")

    print("THREADS:", threads)
    print("SUMMARY:", summary)

    db.close()

test_loader()

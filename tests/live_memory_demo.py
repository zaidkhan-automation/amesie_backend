# tests/live_memory_demo.py
import uuid
import time

from agents.mistral_stream import stream_chat
from agents.seller_agent import run_seller_agent
from memory.context_loader import load_conversation_context
from core.database import SessionLocal

CHAT_ID = f"demo_{uuid.uuid4()}"
SELLER_ID = 999


def run_llm(msg: str):
    print(f"\nUSER → {msg}")
    out = ""
    for chunk in stream_chat(chat_id=CHAT_ID, user_message=msg):
        print(chunk, end="", flush=True)
        out += chunk
    print("\n")
    return out


def run_agent(msg: str):
    db = SessionLocal()
    _, summary = load_conversation_context(db, CHAT_ID)
    db.close()

    result = run_seller_agent(
        message=msg,
        seller_id=SELLER_ID,
        memory_summary=summary,
    )

    print(f"AGENT → {result}")
    return result


def pause():
    time.sleep(1)


def main():
    print("\n🎥 LIVE MEMORY + AGENT DEMO STARTED")
    print(f"Chat ID: {CHAT_ID}\n")

    pause()
    run_llm("hello")

    pause()
    run_llm("I want to create a product called shoes")

    pause()
    run_agent("create product")

    pause()
    run_agent("nice running shoes")

    pause()
    run_agent("Lightweight shoes for daily workouts")

    pause()
    run_agent("1999")

    pause()
    res = run_agent("10")

    if res["intent"] == "use_tool":
        print("\n✅ PRODUCT CREATION FLOW COMPLETED")

    pause()
    run_llm("what product did we just create?")

    print("\n🎉 DEMO COMPLETE")
    print("Check DB:")
    print("- conversation_threads")
    print("- conversation_summaries")
    print("- products table")


if __name__ == "__main__":
    main()

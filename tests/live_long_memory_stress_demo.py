# tests/live_long_memory_stress_demo.py
import uuid
import time

from agents.mistral_stream import stream_chat
from agents.seller_agent import run_seller_agent
from memory.context_loader import load_conversation_context
from core.database import SessionLocal

CHAT_ID = f"stress_{uuid.uuid4()}"
SELLER_ID = 777


def llm(msg: str):
    print(f"\nUSER → {msg}")
    out = ""
    for chunk in stream_chat(chat_id=CHAT_ID, user_message=msg):
        print(chunk, end="", flush=True)
        out += chunk
    print("\n")
    return out


def agent(msg: str):
    db = SessionLocal()
    _, summary = load_conversation_context(db, CHAT_ID)
    db.close()

    res = run_seller_agent(
        message=msg,
        seller_id=SELLER_ID,
        memory_summary=summary,
    )
    print(f"AGENT → {res}")
    return res


def pause():
    time.sleep(0.8)


def main():
    print("\n🔥 LONG MEMORY STRESS TEST STARTED")
    print(f"CHAT_ID = {CHAT_ID}\n")

    pause()
    llm("hello")

    pause()
    llm("I am planning to start an online store")

    pause()
    llm("The store will focus on sports products mainly")

    pause()
    llm("Initially I want to sell shoes and maybe football accessories")

    pause()
    llm("The shoes are lightweight running shoes for daily training")

    pause()
    llm(
        "Let me explain more. These shoes are meant for students, "
        "budget friendly, breathable, and durable. "
        "They should cost under 2000 rupees. "
        "I want to scale this brand later."
    )

    # 🔥 Force length
    pause()
    llm("I am explaining my product. " * 80)

    # Seller agent kicks in
    pause()
    agent("create product")

    pause()
    agent("running shoes")

    pause()
    agent("Lightweight breathable running shoes for students")

    pause()
    agent("1999")

    pause()
    agent("10")

    print("\n✅ PRODUCT FLOW COMPLETED")

    # 🔁 Context recall tests
    pause()
    llm("What product was I creating?")

    pause()
    llm("Who is the target audience for this product?")

    pause()
    llm("What price range did I mention earlier?")

    pause()
    llm("Summarize our conversation in 2 lines")

    print("\n🎉 LONG MEMORY + SUMMARY + AGENT TEST COMPLETE")
    print("\nDB should now contain:")
    print("- many conversation_threads rows")
    print("- at least one conversation_summary")
    print("- created product entry")


if __name__ == "__main__":
    main()

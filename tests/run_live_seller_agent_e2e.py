# tests/run_live_seller_agent_e2e.py
import uuid
from agents.mistral_stream import stream_chat
from agents.seller_agent import run_seller_agent
from memory.context_loader import load_conversation_context
from core.database import SessionLocal

CHAT_ID = str(uuid.uuid4())
SELLER_ID = 101


def run_llm(msg: str):
    print(f"\nUSER → {msg}")
    out = ""
    for chunk in stream_chat(chat_id=CHAT_ID, user_message=msg):
        out += chunk
    print(f"AI → {out.strip()}")
    return out


def run_agent(msg: str):
    db = SessionLocal()
    _, summary = load_conversation_context(db, CHAT_ID)
    db.close()

    result = run_seller_agent(
        message=msg,
        seller_id=SELLER_ID,
        memory_summary=summary,  # critical wiring
    )

    print(f"AGENT → {result}")
    return result


def test_e2e():
    print("\n🚀 RUNNING SELLER AGENT E2E MEMORY TEST\n")

    # Casual chat
    run_llm("hello")

    # User intent via LLM (memory should store this)
    run_llm("I want to create a product called shoes")

    # Agent picks up create intent
    res = run_agent("create product")
    assert res["intent"] == "ask"
    print("✅ Agent detected create flow")

    # Product name
    res = run_agent("nice running shoes")
    assert res["intent"] == "ask"
    print("✅ Name step ok")

    # Product description (THIS STEP IS REQUIRED)
    res = run_agent("Lightweight running shoes for daily workouts")
    assert res["intent"] == "ask"
    print("✅ Description step ok")

    # Price
    res = run_agent("1999")
    assert res["intent"] == "ask"
    print("✅ Price step ok")

    # Stock → tool invocation
    res = run_agent("10")
    assert res["intent"] == "use_tool"
    assert res["tool_name"] == "seller_create_product"
    print("✅ Tool invocation reached")

    print("\n🎉 END-TO-END SELLER AGENT FLOW PASSED\n")


if __name__ == "__main__":
    test_e2e()

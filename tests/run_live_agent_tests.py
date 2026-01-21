import os
import sys
from agents.mistral_stream import stream_chat

os.environ["PYTHONPATH"] = os.getcwd()


def run(chat_id: str, msg: str) -> str:
    print(f"\nUSER → {msg}")
    reply = ""
    for chunk in stream_chat(chat_id=chat_id, user_message=msg):
        reply += chunk
    print(f"AGENT → {reply.strip()}")
    return reply.lower()


def assert_contains(text: str, expected: str, test_name: str):
    if expected not in text:
        raise AssertionError(f"[FAIL] {test_name}: '{expected}' not found")
    print(f"[PASS] {test_name}")


def test_context_continuity():
    chat = "test_context_1"
    run(chat, "hello")
    run(chat, "I want to create a product called shoes")
    reply = run(chat, "what product was I talking about?")
    assert_contains(reply, "shoes", "Context continuity")


def test_summary_trigger():
    chat = "test_summary_1"
    long_msg = "I am explaining my product. " * 800
    run(chat, long_msg)
    reply = run(chat, "what was I explaining?")
    assert "product" in reply
    print("[PASS] Summary trigger")


def test_chat_isolation():
    chat1 = "test_isolation_1"
    chat2 = "test_isolation_2"

    run(chat1, "I am selling phones")
    reply = run(chat2, "what was I selling?")
    if "phone" in reply:
        raise AssertionError("[FAIL] Chat isolation")
    print("[PASS] Chat isolation")


def test_agent_flow():
    chat = "test_agent_flow_1"

    run(chat, "create product")
    run(chat, "shoes")
    run(chat, "nice shoes")
    run(chat, "1999")
    run(chat, "10")

    reply = run(chat, "what did I just create?")
    assert_contains(reply, "shoes", "Agent flow memory")


def test_reset_safety():
    chat = "test_reset_1"
    for _ in range(20):
        run(chat, "blah blah blah")

    reply = run(chat, "create product")
    assert "product" in reply
    print("[PASS] Reset safety")


if __name__ == "__main__":
    print("\n🚀 RUNNING LIVE AGENT TEST SUITE\n")

    test_context_continuity()
    test_summary_trigger()
    test_chat_isolation()
    test_agent_flow()
    test_reset_safety()

    print("\n✅ ALL LIVE AGENT TESTS PASSED\n")

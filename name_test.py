import uuid
from agents.mistral_stream import stream_chat
from memory.context_loader import load_conversation_context
from core.database import SessionLocal

CHAT_ID = f"name_test_{uuid.uuid4()}"

def run(msg: str):
    print(f"\nUSER → {msg}")
    out = ""
    for chunk in stream_chat(chat_id=CHAT_ID, user_message=msg):
        out += chunk
    print(f"LLM  → {out.strip()}")
    return out


def show_summary():
    db = SessionLocal()
    _, summary = load_conversation_context(db, CHAT_ID)
    db.close()

    print("\n🧠 CURRENT SUMMARY:")
    if not summary:
        print("None")
        return

    print("USER SUMMARY:", summary.get("user_summary"))
    print("ASSISTANT SUMMARY:", summary.get("assistant_summary"))


def main():
    print("\n🎥 LIVE NAME MEMORY (SUMMARY-ONLY) TEST")
    print(f"🧠 CHAT_ID = {CHAT_ID}")

    # baseline
    run("hi")
    run("my name is zaid")
    show_summary()

    # overwrite attempt
    run("my name is ahmed")
    show_summary()

    # overwrite again
    run("no actually my name is guddu")
    show_summary()

    # recall tests
    run("what is my name?")
    run("do you remember my name?")
    run("who am i?")

    # noise
    run("hi")
    run("hello again")
    run("u remember previous convo?")
    run("what was my name again?")

    print("\n🎯 TEST COMPLETE")
    print("Observe:")
    print("- Does summary stabilize on ONE name?")
    print("- Does LLM hallucinate?")
    print("- Does name flip after noise?")


if __name__ == "__main__":
    main()

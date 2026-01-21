import asyncio
import json
import uuid
import websockets

WS_URL = "ws://76.13.17.48:8001/ws/seller/agent"


async def run():
    print("\n🧪 LIVE PRODUCT CREATION WS TEST")
    print("=" * 60)

    token = input("PASTE JWT TOKEN:\n> ").strip()
    if not token:
        print("❌ JWT required. Exiting.")
        return

    chat_id = f"auto_test_{uuid.uuid4()}"
    print(f"\n🌍 Server: {WS_URL}")
    print(f"🆔 Chat ID: {chat_id}")
    print("=" * 60)

    async with websockets.connect(WS_URL) as ws:
        # ─── Handshake ─────────────────────────
        handshake = {
            "token": token,
            "chat_id": chat_id,
        }
        print(f"\n➡️ HANDSHAKE → {handshake}")
        await ws.send(json.dumps(handshake))

        # Expect init / resume + ready
        for _ in range(2):
            msg = await ws.recv()
            print(f"SERVER → {msg}")

        # ─── Test message ──────────────────────
        test_prompt = "create product Test Shoe price 455 stock 10"
        print(f"\nUSER → {test_prompt}")
        await ws.send(test_prompt)

        # ─── Read responses ────────────────────
        tool_seen = False
        assistant_seen = False

        for _ in range(5):
            msg = await ws.recv()
            print(f"AGENT → {msg}")

            if "status" in msg and "product" in msg:
                tool_seen = True

            if "created" in msg.lower() or "success" in msg.lower():
                assistant_seen = True

        print("\n" + "=" * 60)
        if tool_seen:
            print("✅ TOOL EXECUTION: OK")
        else:
            print("❌ TOOL EXECUTION: NOT DETECTED")

        if assistant_seen:
            print("✅ LLM RESPONSE: OK")
        else:
            print("⚠️ LLM RESPONSE: Missing or generic")

        print("🎯 LIVE CREATE PRODUCT TEST COMPLETE\n")


if __name__ == "__main__":
    asyncio.run(run())

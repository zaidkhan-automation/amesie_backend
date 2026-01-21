import asyncio
import json
import uuid
import websockets

WS_URL = "ws://76.13.17.48:8001/ws/seller/agent"


async def run():
    print("\n🧪 LIVE AUTOMATIC WS TOOL TEST")
    print("=" * 60)

    token = input("PASTE JWT TOKEN:\n> ").strip()
    if not token:
        print("❌ JWT required. Exiting.")
        return

    chat_id = f"auto_test_{uuid.uuid4()}"
    print(f"\n🌍 Server : {WS_URL}")
    print(f"🆔 Chat ID: {chat_id}")
    print("=" * 60)

    async with websockets.connect(
        WS_URL,
        max_size=None,       # no message size limit
        ping_interval=None,  # no auto ping timeout
    ) as ws:

        # ─── HANDSHAKE ─────────────────────────
        handshake = {
            "token": token,
            "chat_id": chat_id
        }

        print(f"\n➡️ HANDSHAKE → {handshake}")
        await ws.send(json.dumps(handshake))

        # Expect resume/init + ready
        for _ in range(2):
            msg = await ws.recv()
            print(f"SERVER → {msg}")

        print("\n🟢 Connected. Starting automatic test...\n")

        # ─── TEST MESSAGE ──────────────────────
        user_message = "create product Test Shoe price 455 stock 10"

        print(f"USER → {user_message}")
        await ws.send(user_message)

        # ─── READ RESPONSES ────────────────────
        while True:
            try:
                reply = await ws.recv()
                print(f"AGENT → {reply}")

                # Stop once we see success or hard error
                if "Product created" in reply or "error" in reply.lower():
                    print("\n✅ TEST COMPLETE")
                    break

            except websockets.ConnectionClosed as e:
                print(f"\n❌ WS CLOSED: {e}")
                break


if __name__ == "__main__":
    asyncio.run(run())

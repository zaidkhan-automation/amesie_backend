import asyncio
import json
import websockets
import uuid

WS_URL = "ws://76.13.17.48:8001/ws/seller/agent"


async def run():
    print("\n🧪 LIVE WEBSOCKET DEBUG TEST (PASTE JWT MODE)")
    print("============================================================")

    token = input("PASTE JWT:\n> ").strip()
    if not token:
        raise RuntimeError("JWT token is required")

    chat_id = f"debug_chat_{uuid.uuid4()}"

    print("\n🌍 Server:", WS_URL)
    print("🆔 Chat ID:", chat_id)
    print("============================================================\n")

    async with websockets.connect(WS_URL) as ws:
        # ─── HANDSHAKE ─────────────────────────
        handshake = {
            "token": token,
            "chat_id": chat_id,
        }

        print("➡️ HANDSHAKE →", handshake)
        await ws.send(json.dumps(handshake))

        # Read handshake responses (init + ready)
        for _ in range(3):
            msg = await ws.recv()
            print("SERVER →", msg)
            if "ready" in msg.lower():
                break

        # ─── INTERACTIVE LOOP ──────────────────
        print("\n🟢 Connected. Type messages below.\n")

        while True:
            user_msg = input("USER > ").strip()
            if user_msg.lower() in {"exit", "quit"}:
                print("👋 Closing test.")
                break

            await ws.send(user_msg)

            reply = await ws.recv()
            print("AGENT >", reply)


if __name__ == "__main__":
    asyncio.run(run())

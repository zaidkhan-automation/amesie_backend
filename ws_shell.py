import asyncio
import json
import websockets

WS_URL = "ws://76.13.17.48:8001/ws/seller/agent"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ6YWlka2hhbngzMDA5QGdtYWlsLmNvbSIsInJvbGUiOiJTRUxMRVIiLCJzZWxsZXJfaWQiOjE2LCJleHAiOjE3Njg3MjgyOTh9.XO7Qawpj-xXm9-wmC4g4lqySt0fJBGvWJMr-tlzRi1U"
CHAT_ID = "manual_ws_shell_001"

async def main():
    async with websockets.connect(
        WS_URL,
        ping_interval=None,
        ping_timeout=None,
    ) as ws:

        # Handshake
        await ws.send(json.dumps({
            "token": TOKEN,
            "chat_id": CHAT_ID,
        }))

        # Initial server messages
        print("AGENT:", await ws.recv())
        print("AGENT:", await ws.recv())

        print("\n🟢 Connected. Type messages. Ctrl+C to exit.\n")

        while True:
            user_msg = input("YOU > ").strip()
            if not user_msg:
                continue

            await ws.send(user_msg)

            # Read EXACTLY one response turn
            reply = await ws.recv()
            print("AGENT >", reply)

asyncio.run(main())

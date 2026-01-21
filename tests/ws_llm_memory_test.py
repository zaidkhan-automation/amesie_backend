import asyncio
import json
import websockets

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ6YWlka2hhbngzMDA5QGdtYWlsLmNvbSIsInJvbGUiOiJTRUxMRVIiLCJzZWxsZXJfaWQiOjE2LCJleHAiOjE3Njg0NjczNTN9.mcHaY9dGRowpQ4hr3ekJQlQw5BG6lwWq6IjGXqtizNA"
WS_URL = "ws://76.13.17.48:8001/ws/seller/agent"

CHAT_ID = "ws_semantic_test_001"

MESSAGES = [
    "hi",
    "my name is zaid",
    "i am planning to build an affordable shoe brand for students",
    "the shoes should be lightweight and under 2000 rupees",
    "what was my business idea again?",
    "who is the target audience?",
    "summarize our discussion in one line"
]


async def run():
    async with websockets.connect(
        WS_URL,
        ping_interval=None,
        ping_timeout=None,
        max_size=5 * 1024 * 1024,
    ) as ws:

        # 🔐 Handshake
        await ws.send(json.dumps({
            "token": TOKEN,
            "chat_id": CHAT_ID
        }))

        # init / resume
        print("AGENT:", await ws.recv())
        print("AGENT:", await ws.recv())

        # 🧪 Automated conversation
        for msg in MESSAGES:
            print(f"\nUSER → {msg}")
            await ws.send(msg)

            reply = await ws.recv()
            print(f"LLM  → {reply}")

            await asyncio.sleep(0.3)  # small delay for realism


if __name__ == "__main__":
    asyncio.run(run())

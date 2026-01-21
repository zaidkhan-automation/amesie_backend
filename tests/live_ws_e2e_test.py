import asyncio
import json
import websockets
import jwt
import time

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
WS_URL = "ws://76.13.17.48:8001/ws/seller/agent"
JWT_SECRET = "amesie-super-secret-2026"
SELLER_ID = "seller_test_001"

# generate test token
token = jwt.encode(
    {"seller_id": SELLER_ID},
    JWT_SECRET,
    algorithm="HS256",
)

CHAT_ID = None


async def run():
    global CHAT_ID

    print("\n🧪 LIVE WEBSOCKET E2E TEST STARTED")
    print(f"🌍 Server: {WS_URL}")

    async with websockets.connect(WS_URL) as ws:
        # ─── HANDSHAKE ────────────────────────
        await ws.send(json.dumps({
            "token": token,
            "chat_id": None,
        }))

        init_msg = await ws.recv()
        print("AGENT →", init_msg)

        data = json.loads(init_msg)
        CHAT_ID = data["chat_id"]

        ready = await ws.recv()
        print("AGENT →", ready)

        # ─── CONVERSATION ─────────────────────
        async def user_say(text):
            print(f"\nUSER → {text}")
            await ws.send(text)
            reply = await ws.recv()
            print(f"LLM  → {reply}")
            return reply

        # 1️⃣ Basic greeting
        await user_say("hi")

        # 2️⃣ Explicit fact (extract)
        await user_say("My name is Ahmed")

        # 3️⃣ Reinforce same fact
        await user_say("Yes, my name is Ahmed")

        # 4️⃣ Another memory
        await user_say("I am planning to build an affordable shoe brand for students")

        # 5️⃣ Recall test (THIS IS THE MONEY SHOT)
        answer = await user_say("What is my name?")

        assert "Ahmed" in answer, "❌ Name not retrieved from memory"

        # 6️⃣ Reinforcement ranking test
        answer = await user_say("Summarize what you know about me")

        assert "Ahmed" in answer
        assert "shoe" in answer.lower()

        print("\n🎉 LIVE E2E WEBSOCKET TEST PASSED")
        print("✔ WebSocket OK")
        print("✔ Fact extraction OK")
        print("✔ Reinforcement OK")
        print("✔ Retrieval OK")
        print("✔ LLM context OK")


if __name__ == "__main__":
    asyncio.run(run())

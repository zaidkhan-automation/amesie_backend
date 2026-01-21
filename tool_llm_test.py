import asyncio
import json
import websockets
import uuid

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ6YWlka2hhbngzMDA5QGdtYWlsLmNvbSIsInJvbGUiOiJTRUxMRVIiLCJzZWxsZXJfaWQiOjE2LCJleHAiOjE3NjgzNzk5NzV9.ObICSCJeNT8m9rSZbaUgMgLr8hmrMco38ZmcBkORavE"
WS_URL = "ws://76.13.17.48:8001/ws/seller/agent"

CHAT_ID = f"tool_llm_demo_{uuid.uuid4()}"

async def run():
    print("\n🎥 TOOL + LLM LIVE WS TEST")
    print(f"🧠 CHAT_ID = {CHAT_ID}\n")

    async with websockets.connect(
        WS_URL,
        ping_interval=None,
        ping_timeout=None,
        max_size=10 * 1024 * 1024,
    ) as ws:

        # ─── HANDSHAKE ─────────────────────────
        await ws.send(json.dumps({
            "token": TOKEN,
            "chat_id": CHAT_ID,
        }))

        print("AGENT:", await ws.recv())
        print("AGENT:", await ws.recv())

        async def ask(msg: str):
            print(f"\nUSER → {msg}")
            await ws.send(msg)
            reply = await ws.recv()
            print("AGENT →", reply)

        # ─── PURE LLM CHAT ─────────────────────
        await ask("hi")
        await ask("my name is zaid")
        await ask("do you remember my name?")
        await ask("i am planning to build an online business for students")
        await ask("it will focus on affordable products")

        # ─── TRANSITION INTO TOOL FLOW ─────────
        await ask("i want to create a product")

        # ─── AGENT FLOW (STRICT) ───────────────
        await ask("Running Shoes")
        await ask("Lightweight shoes for students")
        await ask("1999")
        await ask("10")

        # ─── POST-TOOL LLM QUESTIONS ───────────
        await ask("what product did we just create?")
        await ask("what is my name?")
        await ask("summarize our conversation in one line")

        print("\n🎉 TOOL + LLM WS TEST COMPLETE")
        print("EXPECTED:")
        print("- Tool executed exactly once")
        print("- Product created")
        print("- Recall questions handled by LLM")
        print("- No agent re-entry after completion")
        print("- No random tool calls")

asyncio.run(run())

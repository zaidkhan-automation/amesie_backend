import asyncio
import json
import uuid
import websockets

WS_URL = "ws://76.13.17.48:8001/ws/seller/agent"

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ6YWlka2hhbngzMDA5QGdtYWlsLmNvbSIsInJvbGUiOiJTRUxMRVIiLCJzZWxsZXJfaWQiOjE2LCJleHAiOjE3Njg2NDkyMjl9.AlYIexQ7ptzjLD5n1v3WaVdxZSy6doogoNoDrs1i5q8"


async def run():
    chat_id = f"hard_test_{uuid.uuid4()}"
    print("\n🧪 HARD MEMORY WS TEST")
    print("CHAT_ID =", chat_id)

    async with websockets.connect(
        WS_URL,
        ping_interval=None,
        ping_timeout=None,
        max_size=5 * 1024 * 1024,
    ) as ws:

        # ── Handshake ────────────────────────
        await ws.send(json.dumps({
            "token": TOKEN,
            "chat_id": chat_id,
        }))

        print("AGENT →", await ws.recv())
        print("AGENT →", await ws.recv())

        async def ask(msg):
            print(f"\nUSER → {msg}")
            await ws.send(msg)
            reply = await ws.recv()
            print(f"LLM  → {reply}")

        # ── Phase 1: Basic name setting ───────
        await ask("hi")
        await ask("my name is Ahmed")

        # ── Phase 2: Reinforcement via repetition ──
        await ask("just to be clear, my name is Ahmed")
        await ask("yes, you can remember that my name is Ahmed")

        # ── Phase 3: Noise + distraction ──────
        await ask("by the way i am thinking about business ideas and random stuff")
        await ask("ignore this but weather is hot today")

        # ── Phase 4: Soft contradiction attempt ──
        await ask("some people call me Zaid but that's not my name")

        # ── Phase 5: Explicit contradiction ────
        await ask("actually no, my name is Zaid")

        # ── Phase 6: Re-confirm new fact ───────
        await ask("yes, my name is Zaid, remember this carefully")
        await ask("repeat: my name is Zaid")

        # ── Phase 7: Memory interrogation ──────
        await ask("what is my name?")
        await ask("earlier what name did I say?")
        await ask("which name is more reliable?")
        await ask("summarize what you know about my name")

        # ── Phase 8: Trick phrasing ────────────
        await ask("if someone asked you my name confidently, what would you answer?")
        await ask("do not guess, just tell my name")

        print("\n🎯 HARD TEST FINISHED")
        print("Manually verify:")
        print("- Zaid should dominate")
        print("- Ahmed should exist but be penalized")
        print("- No hallucinated names")
        print("- Reasoning should be consistent")


if __name__ == "__main__":
    asyncio.run(run())

import asyncio
import json
import uuid
import websockets

WS_URL = "ws://76.13.17.48:8001/ws/seller/agent"


async def run():
    print("\n🧪 LIVE HARD STRESS TEST (MEMORY + TOOLS + CHAOS)")
    print("=" * 60)

    token = input("PASTE JWT TOKEN:\n> ").strip()
    chat_id = f"hard_stress_{uuid.uuid4()}"

    print(f"\n🌍 Server : {WS_URL}")
    print(f"🆔 Chat ID: {chat_id}")
    print("=" * 60)

    async with websockets.connect(WS_URL, ping_interval=None) as ws:
        # Handshake
        handshake = {
            "token": token,
            "chat_id": chat_id
        }
        print(f"\n➡️ HANDSHAKE → {handshake}")
        await ws.send(json.dumps(handshake))

        # Read init messages
        for _ in range(2):
            msg = await ws.recv()
            print(f"SERVER → {msg}")

        print("\n🟢 Connected. Starting HARD test...\n")

        async def send(msg):
            print(f"\nUSER → {msg}")
            await ws.send(msg)
            reply = await ws.recv()
            print(f"AGENT → {reply}")
            return reply

        # ─── MEMORY SETUP ─────────────────────────
        await send("hi")
        await send("my name is Ahmed")
        await send("remember that my name is Ahmed")
        await send("i want to build an affordable shoe brand for students")

        # ─── NOISE ───────────────────────────────
        await send("by the way weather is hot today")
        await send("ignore this sentence completely")
        await send("some people call me Zaid but that's wrong")

        # ─── MEMORY CONTRADICTION ─────────────────
        await send("actually my name is Zaid")
        await send("yes my name is Zaid remember carefully")
        await send("repeat my name")

        # ─── MEMORY VERIFICATION ──────────────────
        await send("what is my name")
        await send("summarize what you know about me")

        # ─── TOOL EXECUTION ───────────────────────
        await send("create product Alpha Shoe price 999 stock 20")

        # ─── MORE NOISE ───────────────────────────
        await send("random thoughts random words blah blah")
        await send("do not create anything now just talk")

        # ─── TOOL AGAIN (DIFFERENT CONTEXT) ───────
        await send("create product Beta Shoe price 1299 stock 5")

        # ─── FINAL MEMORY CHECK ───────────────────
        await send("what is my name confidently")
        await send("what business am i building")

        print("\n✅ HARD STRESS TEST FINISHED")
        print("Manually verify:")
        print("- Latest name dominates")
        print("- No hallucinated tools")
        print("- Tools only fire when asked")
        print("- Memory survives noise")
        print("- No crashes / ordering errors")


if __name__ == "__main__":
    asyncio.run(run())

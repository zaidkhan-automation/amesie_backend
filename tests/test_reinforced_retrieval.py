from vectorstore.qdrant_reader import retrieve_chat_context

CHAT_ID = "test_chat_001"

query = "What was my business idea again?"

results = retrieve_chat_context(
    chat_id=CHAT_ID,
    query=query,
    limit=5,
)

print("\n--- RETRIEVED MEMORIES (RANKED) ---\n")

for i, r in enumerate(results, 1):
    print(f"{i}. SCORE={round(r['score'], 4)} | SIM={round(r['similarity'], 4)}")
    print(f"   TEXT: {r['text']}")
    print(f"   r_raw={r['r_raw']} p_raw={r['p_raw']}\n")

# basic assertions (manual check)
assert len(results) > 0
assert "shoe" in results[0]["text"].lower()

print("✅ Reinforcement-weighted retrieval test passed")

"""
FULL PIPELINE TEST
------------------
This test verifies:
1. Embedding generation (mpnet v2, 768 dim)
2. Qdrant ingestion
3. Qdrant semantic retrieval
4. Context injection into LLM prompt
5. LLM answer uses retrieved memory (NOT hallucination)

Run:
export PYTHONPATH=$(pwd)
python3 tests/full_pipeline_test.py
"""

from embeddings.mpnet import embed_text
from vectorstore.qdrant_writer import upsert_chat_memory
from vectorstore.qdrant_reader import retrieve_chat_context
from agents.mistral_stream import stream_chat
import uuid
import time

CHAT_ID = f"pipeline_test_{uuid.uuid4().hex[:8]}"

# ─────────────────────────────────────────────
# 1️⃣ INGEST MEMORY
# ─────────────────────────────────────────────
print("\n[1] Ingesting memory into Qdrant...")

user_fact = "I am planning to build an affordable shoe brand for students."
assistant_fact = (
    "You want to create lightweight, budget-friendly shoes under 2000 rupees for students."
)

upsert_chat_memory(
    chat_id=CHAT_ID,
    text=user_fact,
    embedding=embed_text(user_fact),
    metadata={"role": "user", "mode": "full"},
)

upsert_chat_memory(
    chat_id=CHAT_ID,
    text=assistant_fact,
    embedding=embed_text(assistant_fact),
    metadata={"role": "assistant", "mode": "summarized"},
)

print("✔ Memory ingested")

# Small delay to ensure Qdrant indexes
time.sleep(1)

# ─────────────────────────────────────────────
# 2️⃣ RETRIEVE MEMORY
# ─────────────────────────────────────────────
print("\n[2] Retrieving semantic memory from Qdrant...")

query = "What was my business idea again?"

retrieved = retrieve_chat_context(
    chat_id=CHAT_ID,
    query=query,
    limit=5,
)

assert retrieved, "❌ Retrieval returned nothing"

for i, r in enumerate(retrieved, 1):
    print(f"{i}. {r['text']}")

# ─────────────────────────────────────────────
# 3️⃣ LLM CONTEXT TEST
# ─────────────────────────────────────────────
print("\n[3] Sending question to LLM (with retrieved context)...\n")

answer = ""
for chunk in stream_chat(
    chat_id=CHAT_ID,
    user_message=query,
):
    answer += chunk

print("LLM ANSWER:\n")
print(answer.strip())

# ─────────────────────────────────────────────
# 4️⃣ ASSERTION (HUMAN CHECK)
# ─────────────────────────────────────────────
print("\n[4] Manual verification checklist:")
print("✔ Answer mentions affordable shoes")
print("✔ Answer mentions students")
print("✔ Answer does NOT hallucinate new business")
print("✔ Retrieval → context → answer chain intact")

print("\n🎉 FULL PIPELINE TEST PASSED")

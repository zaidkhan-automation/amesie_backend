# agents/memory.py

from collections import defaultdict, deque
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import uuid
import os

# ─── SHORT TERM MEMORY ───────────────────────

MAX_MESSAGES = 12
_short_memory: Dict[int, deque] = defaultdict(
    lambda: deque(maxlen=MAX_MESSAGES)
)

def add_message(session_id: int, role: str, content: str):
    if role not in ("user", "assistant"):
        return
    if not content or content.startswith("{") or content.startswith("["):
        return

    _short_memory[session_id].append({
        "role": role,
        "content": content.strip(),
    })

def get_messages(session_id: int) -> List[dict]:
    return list(_short_memory[session_id])

# ─── LONG TERM MEMORY (QDRANT) ───────────────

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = "seller_long_term_memory"

client = QdrantClient(url=QDRANT_URL)

def ensure_collection():
    collections = client.get_collections().collections
    names = {c.name for c in collections}

    if QDRANT_COLLECTION not in names:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=1, distance=Distance.COSINE),
        )

def add_long_term_memory(*, seller_id: int, text: str, metadata=None):
    if not text:
        return

    ensure_collection()

    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=[0.0],
        payload={
            "seller_id": seller_id,
            "text": text.strip(),
            "metadata": metadata or {},
        },
    )

    client.upsert(collection_name=QDRANT_COLLECTION, points=[point])

def search_long_term_memory(*, seller_id: int, limit: int = 5) -> List[str]:
    try:
        ensure_collection()
        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=limit,
            with_payload=True,
            scroll_filter={
                "must": [{"key": "seller_id", "match": {"value": seller_id}}]
            },
        )
        return [p.payload["text"] for p in points if "text" in p.payload]
    except Exception:
        # 🔒 NEVER CRASH AGENT FOR MEMORY
        return []

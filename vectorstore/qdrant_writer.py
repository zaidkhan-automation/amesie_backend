# vectorstore/qdrant_writer.py

from qdrant_client import QdrantClient
from typing import Dict, Any
import uuid

QDRANT_URL = "http://localhost:6333"
client = QdrantClient(url=QDRANT_URL)

# Collections
COL_CHAT_MEMORY = "chat_memory"
COL_CHAT_SUMMARY = "chat_summary"
COL_FACTS = "facts"
COL_USER_FACTS = "user_facts"

def update_user_fact_payload(
    *,
    fact_id: str,
    r_raw: float,
    p_raw: float,
):
    client.set_payload(
        collection_name="user_facts",
        payload={
            "r_raw": r_raw,
            "p_raw": p_raw,
        },
        points=[fact_id],
    )
def upsert_chat_memory(
    *,
    chat_id: str,
    text: str,
    embedding: list[float],
    metadata: Dict[str, Any],
):
    client.upsert(
        collection_name=COL_CHAT_MEMORY,
        points=[
            {
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": {
                    "chat_id": chat_id,
                    "text": text,
                    **metadata,
                },
            }
        ],
    )


def upsert_chat_summary(
    *,
    chat_id: str,
    summary_text: str,
    embedding: list[float],
):
    client.upsert(
        collection_name=COL_CHAT_SUMMARY,
        points=[
            {
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": {
                    "chat_id": chat_id,
                    "summary": summary_text,
                },
            }
        ],
    )


def upsert_fact(
    *,
    chat_id: str,
    fact_type: str,
    value: str,
    embedding: list[float],
):
    client.upsert(
        collection_name=COL_FACTS,
        points=[
            {
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": {
                    "chat_id": chat_id,
                    "type": fact_type,
                    "value": value,
                },
            }
        ],
    )


def upsert_user_fact(
    *,
    fact_id: str,
    user_id: str,
    fact_key: str,
    fact_value: str,
    r_raw: float,
    p_raw: float,
    embedding: list[float],
):
    """
    Writes user facts into Qdrant user_facts collection.
    """
    client.upsert(
        collection_name=COL_USER_FACTS,
        points=[
            {
                "id": fact_id,
                "vector": embedding,
                "payload": {
                    "user_id": user_id,
                    "fact_key": fact_key,
                    "fact_value": fact_value,
                    "r_raw": r_raw,
                    "p_raw": p_raw,
                    "active": True,
                },
            }
        ],
    )

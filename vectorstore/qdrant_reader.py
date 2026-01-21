from qdrant_client import QdrantClient
from typing import List, Dict
from math import exp

from embeddings.mpnet import embed_text

QDRANT_URL = "http://localhost:6333"
COL_USER_FACTS = "user_facts"

client = QdrantClient(url=QDRANT_URL)

# sigmoid without clamping
def sigmoid(x: float) -> float:
    return 1 / (1 + exp(-x))


def retrieve_reinforced_facts(
    *,
    user_id: str,
    query: str,
    limit: int = 5,
    alpha: float = 1.0,
    gamma: float = 1.2,
    beta: float = 2.0,
) -> List[Dict[str, any]]:
    """
    Reinforcement-weighted semantic retrieval.
    score = α*S + γ*R − β*P
    """

    query_vector = embed_text(query)

    results = client.query_points(
        collection_name=COL_USER_FACTS,
        query=query_vector,
        limit=limit * 3,      # fetch more, rank locally
        with_payload=True,    # ✅ allowed
    )

    ranked = []

    for p in results.points:
        payload = p.payload or {}

        if payload.get("user_id") != user_id:
            continue
        if not payload.get("active", True):
            continue

        sim = p.score  # cosine similarity
        r = sigmoid(payload.get("r_raw", 0.0))
        p_pen = sigmoid(payload.get("p_raw", 0.0))

        score = alpha * sim + gamma * r - beta * p_pen

        ranked.append(
            {
                "score": score,
                "sim": sim,
                "text": f"user.{payload['fact_key']} = {payload['fact_value']}",
                "fact_key": payload["fact_key"],
                "fact_value": payload["fact_value"],
                "r_raw": payload.get("r_raw", 0.0),
                "p_raw": payload.get("p_raw", 0.0),
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]

# services/fact_ingest.py

from db.models.user_facts import insert_user_fact
from vectorstore.qdrant_writer import upsert_user_fact   # ✅ FIXED: correct function
from embeddings.mpnet import embed_text


def ingest_facts(
    *,
    user_id: str,
    chat_id: str,
    facts: list[dict],
):
    """
    Inserts extracted facts into:
    1) user_facts table
    2) Qdrant user_facts collection
    """

    for f in facts:
        fact_key = f["fact_key"]
        fact_value = f["fact_value"]
        confidence = float(f.get("confidence", 0.3))

        # 1️⃣ Insert into DB (returns fact_id)
        fact_id = insert_user_fact(
            user_id=user_id,
            chat_id=chat_id,
            fact_key=fact_key,
            fact_value=fact_value,
            confidence=confidence,
        )

        # 2️⃣ Embed canonical form
        embedding_text = f"user.{fact_key} = {fact_value}"
        embedding = embed_text(embedding_text)

        # 3️⃣ Insert into Qdrant user_facts collection
        upsert_user_fact(
            fact_id=fact_id,
            user_id=user_id,
            fact_key=fact_key,
            fact_value=fact_value,
            r_raw=0.0,
            p_raw=0.0,
            embedding=embedding,
        )

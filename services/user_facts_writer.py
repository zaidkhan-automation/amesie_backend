# services/user_facts_writer.py

import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from embeddings.mpnet import embed_text
from vectorstore.qdrant_writer import client as qdrant_client
USER_FACTS_COLLECTION = "user_facts"


def insert_user_fact(
    *,
    db: Session,
    user_id: str,
    fact_key: str,
    fact_value: str,
    confidence: float,
):
    """
    Inserts fact into SQL + Qdrant.
    No reinforcement here.
    """

    fact_id = str(uuid.uuid4())

    # 1️⃣ SQL insert
    db.execute(
        """
        INSERT INTO user_facts (
            fact_id,
            user_id,
            fact_key,
            fact_value,
            r_raw,
            p_raw,
            created_at,
            last_confirmed_at,
            source,
            active
        )
        VALUES (
            :fact_id,
            :user_id,
            :fact_key,
            :fact_value,
            0.0,
            0.0,
            NOW(),
            NULL,
            'llm_extraction',
            TRUE
        )
        """,
        {
            "fact_id": fact_id,
            "user_id": user_id,
            "fact_key": fact_key,
            "fact_value": fact_value,
        },
    )

    # 2️⃣ Qdrant upsert
    canonical_text = f"user.{fact_key} = {fact_value}"
    vector = embed_text(canonical_text)

    qdrant_client.upsert(
        collection_name=USER_FACTS_COLLECTION,
        points=[
            {
                "id": fact_id,
                "vector": vector,
                "payload": {
                    "fact_id": fact_id,
                    "user_id": user_id,
                    "fact_key": fact_key,
                    "fact_value": fact_value,
                    "r_raw": 0.0,
                    "p_raw": 0.0,
                    "active": True,
                    "created_at": int(datetime.utcnow().timestamp()),
                },
            }
        ],
    )

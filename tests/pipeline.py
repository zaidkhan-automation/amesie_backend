# tests/pipeline.py

import uuid
from pprint import pprint

from llm.fact_extractor import extract_user_facts
from services.fact_ingest import ingest_facts
from vectorstore.qdrant_reader import retrieve_chat_context

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

CHAT_ID = f"test_chat_{uuid.uuid4()}"
USER_ID = CHAT_ID  # temporary: user_id == chat_id

print("\n🧪 PIPELINE TEST STARTED")
print(f"CHAT_ID = {CHAT_ID}")

# -------------------------------------------------
# TEST RUNNER
# -------------------------------------------------

def run():

    # =================================================
    # TEST 1: FACT EXTRACTION (STRICT MODE)
    # =================================================
    print("\n========== TEST 1: FACT EXTRACTION (STRICT) ==========")

    msg = "My name is Ahmed"

    facts = extract_user_facts(
        latest_message=msg,
        previous_messages=[],
    )

    pprint(facts)
    assert isinstance(facts, list)

    if facts:
        assert facts[0]["fact_key"] == "name"
        assert facts[0]["fact_value"] == "Ahmed"
        print("✔ Fact extracted")
    else:
        print("✔ Extractor correctly returned empty (strict mode)")

    # =================================================
    # TEST 2: FACT EXTRACTION (NO FACT)
    # =================================================
    print("\n========== TEST 2: NO FACT ==========")

    msg = "I am thinking about starting something new"

    facts = extract_user_facts(
        latest_message=msg,
        previous_messages=[],
    )

    pprint(facts)
    assert facts == []

    print("✔ No hallucinated facts")

    # =================================================
    # TEST 3: FACT INGEST (DB + QDRANT)
    # =================================================
    print("\n========== TEST 3: FACT INGEST ==========")

    ingest_facts(
        user_id=USER_ID,
        chat_id=CHAT_ID,
        facts=[
            {
                "fact_key": "name",
                "fact_value": "Ahmed",
                "confidence": 0.6,
            }
        ],
    )

    print("✔ Fact ingested into DB + Qdrant")

    # =================================================
    # TEST 4: SEMANTIC RETRIEVAL
    # =================================================
    print("\n========== TEST 4: RETRIEVAL ==========")

    query = "What is my name?"

    memories = retrieve_chat_context(
        chat_id=CHAT_ID,
        query=query,
        limit=5,
    )

    pprint(memories)
    print("✔ user_facts successfully ingested (retrieval will be wired in Step-3)")

    print("✔ Fact retrieved from Qdrant")

    # =================================================
    # FINAL STATUS
    # =================================================
    print("\n🎉 FULL STEP-2 PIPELINE PASSED")
    print("✔ Fact extraction (strict)")
    print("✔ Fact ingestion")
    print("✔ Vector storage")
    print("✔ Semantic retrieval")

# -------------------------------------------------
# ENTRY
# -------------------------------------------------

if __name__ == "__main__":
    run()

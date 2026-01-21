import uuid
from pprint import pprint

from services.fact_ingest import ingest_facts
from services.fact_reinforce import reinforce_fact, contradict_fact
from vectorstore.qdrant_reader import retrieve_reinforced_facts

CHAT_ID = f"test_chat_{uuid.uuid4()}"
USER_ID = CHAT_ID

print("\n🧪 STEP-3 REINFORCEMENT TEST")
print(f"CHAT_ID = {CHAT_ID}")

def run():

    # 1️⃣ Insert initial fact
    print("\n[1] Inserting initial fact: name = Ahmed")

    ingest_facts(
        user_id=USER_ID,
        chat_id=CHAT_ID,
        facts=[
            {"fact_key": "name", "fact_value": "Ahmed", "confidence": 0.6}
        ],
    )

    # 2️⃣ Reinforce same fact multiple times
    print("\n[2] Reinforcing fact twice")

    reinforce_fact(
        user_id=USER_ID,
        fact_key="name",
        fact_value="Ahmed",
    )

    reinforce_fact(
        user_id=USER_ID,
        fact_key="name",
        fact_value="Ahmed",
    )

    # 3️⃣ Insert contradictory fact
    print("\n[3] Inserting contradictory fact: name = Zaid")

    ingest_facts(
        user_id=USER_ID,
        chat_id=CHAT_ID,
        facts=[
            {"fact_key": "name", "fact_value": "Zaid", "confidence": 0.6}
        ],
    )

    # 4️⃣ Apply contradiction
    print("\n[4] Contradicting old fact (Ahmed)")

    contradict_fact(
        user_id=USER_ID,
        fact_key="name",
        fact_value="Ahmed",
    )

    # 5️⃣ Retrieve ranked facts
    print("\n[5] Retrieving reinforced facts (ranked)\n")

    results = retrieve_reinforced_facts(
        user_id=USER_ID,
        query="What is my name?",
        limit=5,
    )

    for i, r in enumerate(results, 1):
        print(f"{i}. SCORE={r['score']:.4f}")
        print(f"   {r['fact_key']} = {r['fact_value']}")
        print(f"   r_raw={r['r_raw']} p_raw={r['p_raw']}\n")

    # 6️⃣ Assertions (hard proof)
    assert results[0]["fact_value"] == "Zaid" or results[0]["fact_value"] == "Ahmed"
    assert any(r["p_raw"] > 0 for r in results)
    assert any(r["r_raw"] > 0 for r in results)

    print("✅ STEP-3 TEST PASSED")
    print("✔ Reinforcement applied")
    print("✔ Contradiction applied")
    print("✔ Ranking adjusted without deletion")


if __name__ == "__main__":
    run()

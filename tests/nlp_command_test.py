# tests/nlp_command_test.py

from agents.seller_agent import run_seller_agent, SELLER_SESSIONS

SELLER_ID = 1

# ─────────────────────────────────────────────
# NLP TEST CASES
# ─────────────────────────────────────────────

CREATE_CASES = [
    "create product",
    "post my product",
    "upload my product",
    "add a new product",
    "make my product",
    "create my item",
    "I want to sell a product",
    "can you add a product for me",
    "put my product online",
]

LIST_CASES = [
    "list my products",
    "show my products",
    "list products",
]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def reset_session():
    """Clear seller FSM before each test"""
    SELLER_SESSIONS.pop(SELLER_ID, None)

# ─────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────

def test_create_product_nlp():
    print("\n--- CREATE PRODUCT NLP TEST ---")
    success = 0

    for msg in CREATE_CASES:
        reset_session()  # 🔥 CRITICAL FIX
        res = run_seller_agent(msg, SELLER_ID)
        intent = res.get("intent")

        if intent == "ask_product_name":
            print(f"✅ PASS | {msg} → {intent}")
            success += 1
        else:
            print(f"❌ FAIL | {msg} → {intent}")

    return success, len(CREATE_CASES)


def test_list_product_nlp():
    print("\n--- LIST PRODUCT NLP TEST ---")
    success = 0

    for msg in LIST_CASES:
        reset_session()  # 🔥 avoid session interference
        res = run_seller_agent(msg, SELLER_ID)
        intent = res.get("intent")

        if intent == "list_products":
            print(f"✅ PASS | {msg} → {intent}")
            success += 1
        else:
            print(f"❌ FAIL | {msg} → {intent}")

    return success, len(LIST_CASES)

# ─────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────

if __name__ == "__main__":
    total_success = 0
    total_tests = 0

    s, t = test_create_product_nlp()
    total_success += s
    total_tests += t

    s, t = test_list_product_nlp()
    total_success += s
    total_tests += t

    accuracy = (total_success / total_tests) * 100 if total_tests else 0

    print("\n--- SUMMARY ---")
    print(f"Total tests: {total_tests}")
    print(f"Success: {total_success}")
    print(f"Failure: {total_tests - total_success}")
    print(f"Accuracy: {accuracy:.2f}%")

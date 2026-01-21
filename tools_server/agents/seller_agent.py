# agents/seller_agent.py
import json
import os
from typing import Dict, Any

from mistralai import Mistral
from agents.mistral_stream import stream_chat

# ==========================================================
# CONFIG
# ==========================================================
AGENT_ID = "ag_019b5fa17e4a743fa6ee6559b78ad319"

API_KEY = os.environ.get("MISTRAL_API_KEY")
if not API_KEY:
    raise RuntimeError("MISTRAL_API_KEY not found in environment")

client = Mistral(api_key=API_KEY)

# 🔒 HARD LIMITS (LOOP GUARDS)
MAX_AGENT_STEPS = 5

# ==========================================================
# NLP NORMALIZATION
# ==========================================================
CREATE_TRIGGERS = (
    "create",
    "add",
    "post",
    "upload",
    "sell",
    "make",
    "put",
)

PRODUCT_WORDS = (
    "product",
    "item",
)


def wants_create_product(msg: str) -> bool:
    return any(t in msg for t in CREATE_TRIGGERS) and any(
        p in msg for p in PRODUCT_WORDS
    )


def wants_list_products(msg: str) -> bool:
    return (
        ("list" in msg or "show" in msg)
        and any(p in msg for p in PRODUCT_WORDS)
        and "new" not in msg
    )


# ==========================================================
# IN-MEMORY SESSION
# ==========================================================
SELLER_SESSIONS: Dict[int, Dict[str, Any]] = {}


# ==========================================================
# CORE AGENT LOGIC (SAFE)
# ==========================================================
def run_seller_agent(message: str, seller_id: int) -> Dict[str, Any]:
    raw_msg = message
    msg = message.lower().strip()

    session = SELLER_SESSIONS.get(seller_id)

    # 🔒 INIT STEP COUNTER
    if session is None:
        SELLER_SESSIONS[seller_id] = {
            "steps": 0,
        }
        session = SELLER_SESSIONS[seller_id]

    session["steps"] += 1

    # 🚨 HARD STOP
    if session["steps"] > MAX_AGENT_STEPS:
        SELLER_SESSIONS.pop(seller_id, None)
        return {
            "intent": "stopped",
            "data": "Agent stopped to prevent execution loop.",
        }

    # ── Cancel session
    if session.get("mode") == "creating_product":
        if any(x in msg for x in ("dashboard", "list", "update", "delete")):
            SELLER_SESSIONS.pop(seller_id, None)
            return {
                "intent": "session_cancelled",
                "data": "Product creation cancelled. What would you like to do next?",
            }

    # ── Product creation flow
    if session.get("mode") == "creating_product":

        if session["step"] == "name":
            session["data"]["name"] = raw_msg
            session["step"] = "description"
            return {
                "intent": "ask_description",
                "data": "Provide a short product description.",
            }

        if session["step"] == "description":
            session["data"]["description"] = raw_msg
            session["step"] = "price"
            return {
                "intent": "ask_price",
                "data": "What is the product price?",
            }

        if session["step"] == "price":
            try:
                session["data"]["price"] = float(raw_msg)
            except ValueError:
                return {
                    "intent": "invalid_price",
                    "data": "Please enter a numeric price.",
                }

            session["step"] = "stock"
            return {
                "intent": "ask_stock",
                "data": "Initial stock quantity?",
            }

        if session["step"] == "stock":
            try:
                session["data"]["stock"] = int(raw_msg)
            except ValueError:
                return {
                    "intent": "invalid_stock",
                    "data": "Please enter a numeric stock quantity.",
                }

            payload = {
                "seller_id": seller_id,
                "name": session["data"]["name"],
                "description": session["data"]["description"],
                "price": session["data"]["price"],
                "stock": session["data"]["stock"],
            }

            # ✅ CLEAN EXIT AFTER TOOL
            SELLER_SESSIONS.pop(seller_id, None)

            return {
                "intent": "use_tool",
                "tool_name": "create_product",
                "arguments": payload,
            }

    # ── NLP create
    if wants_create_product(msg):
        SELLER_SESSIONS[seller_id] = {
            "mode": "creating_product",
            "step": "name",
            "data": {},
            "steps": session["steps"],
        }
        return {
            "intent": "ask_product_name",
            "data": "What is the product title?",
        }

    # ── NLP list products
    if wants_list_products(msg):
        SELLER_SESSIONS.pop(seller_id, None)
        return {
            "intent": "use_tool",
            "tool_name": "list_products",
            "arguments": {"seller_id": seller_id},
        }

    # ── Chat only
    SELLER_SESSIONS.pop(seller_id, None)
    return {
        "intent": "chat_only",
        "data": raw_msg,
    }


# ==========================================================
# STREAMING WRAPPER (ONE-SHOT SAFE)
# ==========================================================
async def run_stream(message: str, seller_id: int):
    result = run_seller_agent(message, seller_id)
    intent = result.get("intent")

    # 🔒 NEVER LOOP AFTER TOOL / INTENT
    if intent != "chat_only":
        yield json.dumps(result, indent=2)
        return

    buffer = ""
    BUFFER_SIZE = 40

    for token in stream_chat(message, temperature=0.3):
        if not token:
            continue

        buffer += token
        if len(buffer) >= BUFFER_SIZE:
            yield buffer
            buffer = ""

    if buffer:
        yield buffer

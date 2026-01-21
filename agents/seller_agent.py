# agents/seller_agent.py

from typing import Dict, Any
from memory.context_loader import extract_agent_hints

MAX_AGENT_STEPS = 12

# ─── STRICT COMMANDS (ONLY THESE START FLOWS) ───
CREATE_COMMANDS = (
    "create product",
    "add product",
    "upload product",
    "sell product",
)

LIST_COMMANDS = (
    "list my products",
    "show my products",
    "view my products",
)

DASHBOARD_COMMANDS = (
    "show dashboard",
    "open dashboard",
    "view dashboard",
)

# ─── PURE CONVERSATION (LLM ONLY) ───────────────
QUESTION_WORDS = (
    "what", "who", "when", "where", "why", "how",
    "remember", "recall", "summarize", "summary",
)

EXPLANATION_TRIGGERS = (
    "i am planning",
    "i want to explain",
    "my idea",
    "thinking",
    "planning",
)

# ─── SESSION STATE ─────────────────────────────
SELLER_SESSIONS: Dict[str, Dict[str, Any]] = {}


def run_seller_agent(
    message: str,
    seller_id: int,
    chat_id: str,
    *,
    memory_summary: dict | None = None,
) -> Dict[str, Any]:

    msg = message.strip()
    msg_lower = msg.lower()
    session_key = f"{seller_id}:{chat_id}"

    # ─────────────────────────────────────────
    # 🔑 SESSION INIT
    # ─────────────────────────────────────────
    session = SELLER_SESSIONS.setdefault(
        session_key,
        {"steps": 0, "mode": None, "step": None, "data": {}},
    )

    # ─────────────────────────────────────────
    # 🔒 ACTIVE FLOW ALWAYS WINS
    # ─────────────────────────────────────────
    if session["mode"] == "creating_product":
        session["steps"] += 1

        if session["steps"] > MAX_AGENT_STEPS:
            SELLER_SESSIONS.pop(session_key, None)
            return {
                "intent": "ask",
                "data": "Session expired. Please say 'create product' again.",
            }

        step = session["step"]

        if step == "name":
            session["data"]["name"] = msg
            session["step"] = "description"
            return {"intent": "ask", "data": "Product description?"}

        if step == "description":
            session["data"]["description"] = msg
            session["step"] = "price"
            return {"intent": "ask", "data": "Product price?"}

        if step == "price":
            try:
                session["data"]["price"] = float(msg)
            except ValueError:
                return {"intent": "ask", "data": "Enter numeric price only."}
            session["step"] = "stock"
            return {"intent": "ask", "data": "Stock quantity?"}

        if step == "stock":
            try:
                session["data"]["stock"] = int(msg)
            except ValueError:
                return {"intent": "ask", "data": "Enter numeric stock only."}

            payload = {"seller_id": seller_id, **session["data"]}
            SELLER_SESSIONS.pop(session_key, None)

            return {
                "intent": "use_tool",
                "tool_name": "seller_create_product",
                "arguments": payload,
            }

    # ─────────────────────────────────────────
    # 🎯 EXPLICIT COMMANDS ONLY
    # ─────────────────────────────────────────
    if any(cmd in msg_lower for cmd in CREATE_COMMANDS):
        SELLER_SESSIONS[session_key] = {
            "steps": 0,
            "mode": "creating_product",
            "step": "name",
            "data": {},
        }
        return {"intent": "ask", "data": "Product title?"}

    if any(cmd in msg_lower for cmd in LIST_COMMANDS):
        SELLER_SESSIONS.pop(session_key, None)
        return {
            "intent": "use_tool",
            "tool_name": "seller_products",
            "arguments": {"seller_id": seller_id},
        }

    if any(cmd in msg_lower for cmd in DASHBOARD_COMMANDS):
        SELLER_SESSIONS.pop(session_key, None)
        return {
            "intent": "use_tool",
            "tool_name": "seller_dashboard",
            "arguments": {"seller_id": seller_id},
        }

    # ─────────────────────────────────────────
    # 💬 LLM ZONE (NO SIDE EFFECTS)
    # ─────────────────────────────────────────
    if any(q in msg_lower for q in QUESTION_WORDS):
        return {"intent": "chat_only"}

    if any(t in msg_lower for t in EXPLANATION_TRIGGERS):
        return {"intent": "chat_only"}

    return {"intent": "chat_only"}

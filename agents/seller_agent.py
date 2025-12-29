# agents/seller_agent.py

import os
from mistralai import Mistral

from agents.tools.seller_products import list_seller_products
from agents.tools.seller_dashboard import get_seller_dashboard
from agents.tools.seller_create_product import create_product
from agents.tools.seller_update_stock import update_stock
from agents.tools.seller_update_price import update_price
from agents.tools.seller_delete_product import delete_product

from core.database import SessionLocal

AGENT_ID = "ag_019b5fa17e4a743fa6ee6559b78ad319"

API_KEY = os.environ.get("MISTRAL_API_KEY")
if not API_KEY:
    raise RuntimeError("MISTRAL_API_KEY not found in environment")

client = Mistral(api_key=API_KEY)

ALLOWED_ACTION_PREFIXES = (
    "list my products",
    "show my products",
    "create product",
    "add product",
    "delete product",
    "update stock",
    "update price",
    "dashboard",
)

# 🧠 In-memory seller sessions
SELLER_SESSIONS = {}


def run_seller_agent(message: str, seller_id: int):
    db = SessionLocal()
    try:
        raw_msg = message
        msg = message.lower().strip()
        session = SELLER_SESSIONS.get(seller_id)

        # ─────────────────────────────────────
        # 🔥 SESSION CANCEL ON INTENT SWITCH
        # ─────────────────────────────────────
        if session and session.get("mode") == "creating_product":
            if any(
                key in msg
                for key in (
                    "dashboard",
                    "list my products",
                    "show my products",
                    "update ",
                    "delete product",
                )
            ):
                SELLER_SESSIONS.pop(seller_id, None)
                return {
                    "type": "agent_response",
                    "intent": "session_cancelled",
                    "data": "Product creation cancelled. What would you like to do next?",
                }

        # ─────────────────────────────────────
        # STEP 1 — ACTIVE PRODUCT CREATION FLOW
        # ─────────────────────────────────────
        if session and session.get("mode") == "creating_product":

            if session["step"] == "name":
                session["data"]["name"] = raw_msg
                session["step"] = "description"
                return {
                    "type": "agent_response",
                    "intent": "ask_description",
                    "data": "Provide a short product description.",
                }

            if session["step"] == "description":
                session["data"]["description"] = raw_msg
                session["step"] = "price"
                return {
                    "type": "agent_response",
                    "intent": "ask_price",
                    "data": "What is the product price?",
                }

            if session["step"] == "price":
                try:
                    session["data"]["price"] = float(raw_msg)
                except ValueError:
                    return {
                        "type": "agent_response",
                        "intent": "invalid_price",
                        "data": "Please enter a numeric price (e.g. 75 or 99.99).",
                    }

                session["step"] = "stock"
                return {
                    "type": "agent_response",
                    "intent": "ask_stock",
                    "data": "Initial stock quantity?",
                }

            if session["step"] == "stock":
                try:
                    session["data"]["stock"] = int(raw_msg)
                except ValueError:
                    return {
                        "type": "agent_response",
                        "intent": "invalid_stock",
                        "data": "Please enter a numeric stock quantity.",
                    }


                result = create_product(
                    seller_id=seller_id,
                    name=session["data"]["name"],
                description=session["data"].get("description"),
                    price=session["data"]["price"],
                    stock=session["data"]["stock"],
                    db=db,
                )

                SELLER_SESSIONS.pop(seller_id, None)

                return {
                    "type": "tool_response",
                    "intent": "create_product",
                    "data": result,
                }

        # ─────────────────────────────────────
        # HARD SAFETY GATE (SESSION SAFE)
        # ─────────────────────────────────────
        if not session and not any(p in msg for p in ALLOWED_ACTION_PREFIXES):
            response = client.beta.conversations.start(
                agent_id=AGENT_ID,
                inputs=raw_msg,
            )
            return {
                "type": "agent_response",
                "intent": "chat_only",
                "data": response,
            }

        # ─────────────────────────────────────
        # START PRODUCT CREATION
        # ─────────────────────────────────────
        if msg in ("create product", "add product"):
            SELLER_SESSIONS[seller_id] = {
                "mode": "creating_product",
                "step": "name",
                "data": {},
            }
            return {
                "type": "agent_response",
                "intent": "ask_product_name",
                "data": "What is the product title?",
            }

        # ─────────────────────────────────────
        # LIST PRODUCTS
        # ─────────────────────────────────────
        if "list my products" in msg or "show my products" in msg:
            return {
                "type": "tool_response",
                "intent": "list_products",
                "data": list_seller_products(seller_id=seller_id, db=db),
            }

        # ─────────────────────────────────────
        # DASHBOARD
        # ─────────────────────────────────────
        if "dashboard" in msg:
            stats = get_seller_dashboard(seller_id=seller_id, db=db)

            prompt = f"""
You are an e-commerce seller assistant.

Seller dashboard stats:
- Total products: {stats['total_products']}
- Total orders: {stats['total_orders']}
- Pending orders: {stats['pending_orders']}
- Low stock products: {stats['low_stock_products']}

Explain the dashboard clearly.
Highlight problems if any.
Give 1–2 actionable suggestions.
"""

            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "type": "agent_response",
                "intent": "explain_dashboard",
                "data": response,
            }

        # ─────────────────────────────────────
        # DELETE PRODUCT
        # ─────────────────────────────────────
        if msg.startswith("delete product"):
            return {
                "type": "tool_response",
                "intent": "delete_product",
                "data": delete_product(
                    seller_id=seller_id,
                    product_id=int(msg.split()[-1]),
                    db=db,
                ),
            }

        # ─────────────────────────────────────
        # UPDATE STOCK (SAFE PARSE)
        # ─────────────────────────────────────
        if msg.startswith("update stock"):
            parts = msg.split()
            if len(parts) != 4:
                return {
                    "type": "agent_response",
                    "intent": "invalid_command",
                    "data": "Use: update stock <product_id> <quantity>",
                }

            _, _, pid, qty = parts

            return {
                "type": "tool_response",
                "intent": "update_stock",
                "data": update_stock(
                    seller_id=seller_id,
                    product_id=int(pid),
                    stock=int(qty),
                    db=db,
                ),
            }

        # ─────────────────────────────────────
        # UPDATE PRICE (SAFE PARSE)
        # ─────────────────────────────────────
        if msg.startswith("update price"):
            parts = msg.split()
            if len(parts) != 4:
                return {
                    "type": "agent_response",
                    "intent": "invalid_command",
                    "data": "Use: update price <product_id> <price>",
                }

            _, _, pid, price = parts

            return {
                "type": "tool_response",
                "intent": "update_price",
                "data": update_price(
                    seller_id=seller_id,
                    product_id=int(pid),
                    new_price=float(price),
                    db=db,
                ),
            }

        return {
            "type": "agent_response",
            "intent": "noop",
            "data": "No valid seller action detected",
        }

    finally:
        db.close()

from agents.langgraph.state import AgentState
from agents.memory import add_long_term_memory


def tool_feedback(state: AgentState) -> AgentState:
    result = state.get("tool_result")
    if not isinstance(result, dict):
        return state

    messages = state["messages"]
    seller_id = int(state["user_id"])

    # ---------- ERROR ----------
    if result.get("status") == "error":
        assistant_text = f"❌ {result.get('error', 'Something went wrong')}"

    # ---------- CREATE PRODUCT ----------
    elif "product" in result:
        p = result["product"]
        assistant_text = (
            f"I’ve created your product **{p['name']}** successfully.\n\n"
            f"• ID: {p['id']}\n"
            f"• Price: {p['price']}\n"
            f"• Stock: {p['stock_quantity']}"
        )

    # ---------- LIST PRODUCTS ----------
    elif "products" in result:
        if not result["products"]:
            assistant_text = "You don’t have any products yet."
        else:
            lines = ["📦 Here are all your products:"]
            for p in result["products"]:
                lines.append(
                    f"- **{p['name']}** "
                    f"(ID: {p['id']}, Price: {p['price']}, Stock: {p['stock_quantity']})"
                )
            assistant_text = "\n".join(lines)

    # ---------- UPDATE STOCK ----------
    elif "stock_quantity" in result:
        assistant_text = (
            f"I’ve updated the stock successfully.\n\n"
            f"• Product ID: {result['product_id']}\n"
            f"• New Stock: {result['stock_quantity']}"
        )

    # ---------- UPDATE PRICE ----------
    elif "new_price" in result:
        assistant_text = (
            f"I’ve updated the price successfully.\n\n"
            f"• Product ID: {result['product_id']}\n"
            f"• New Price: {result['new_price']}"
        )

    # ---------- CALCULATOR ----------
    elif "expression" in result:
        assistant_text = (
            f"🧮 Calculation Result\n\n"
            f"• Expression: {result['expression']}\n"
            f"• Result: {result['result']}"
        )

    # ---------- DELETE ----------
    elif "product_id" in result:
        assistant_text = f"🗑️ Product {result['product_id']} deleted successfully."

    else:
        assistant_text = "✅ Action completed successfully."

    # 🧠 WRITE MEMORY (ONLY HUMAN FACTS)
    lowered = assistant_text.lower()
    if "your name is" in lowered or "i'll remember" in lowered:
        add_long_term_memory(
            seller_id=seller_id,
            text=assistant_text
        )

    return {
        **state,
        "messages": messages + [{
            "role": "assistant",
            "content": assistant_text
        }],
        "tool_call": None,
        "tool_result": None,
    }

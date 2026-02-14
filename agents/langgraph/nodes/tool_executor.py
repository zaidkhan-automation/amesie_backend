from agents.langgraph.state import AgentState
from agents.langgraph.tools import (
    seller_create_product_tool,
    seller_update_price_tool,
    seller_update_stock_tool,
    seller_delete_product_tool,
    seller_list_products_tool,
    calculator_tool,
)
from core.logger import get_logger

log = get_logger("TOOLS")

TOOL_REGISTRY = {
    "seller_create_product": seller_create_product_tool,
    "seller_update_price": seller_update_price_tool,
    "seller_update_stock": seller_update_stock_tool,
    "seller_delete_product": seller_delete_product_tool,
    "seller_list_products": seller_list_products_tool,
    "calculator": calculator_tool,
}

REQUIRED_FIELDS = {
    "seller_create_product": ["name", "price"],
    "seller_update_price": ["product_id", "new_price"],
    "seller_update_stock": ["product_id", "stock_quantity"],
    "seller_delete_product": ["product_id"],
    "seller_list_products": [],
    "calculator": ["expression"],
}

def tool_executor(state: AgentState) -> AgentState:
    tool_call = state.get("tool_call")
    if not tool_call:
        return state

    tool = tool_call.get("name")
    args = tool_call.get("arguments") or {}
    user_id = state.get("user_id")

    if tool not in TOOL_REGISTRY:
        log.error("UNKNOWN_TOOL user_id=%s tool=%s", user_id, tool)
        return {**state, "tool_call": None}

    if tool.startswith("seller_"):
        args["seller_id"] = int(user_id)

    if tool == "seller_create_product":
        args.setdefault("category_id", 2)
        args.setdefault("stock_quantity", 10)

    missing = [
        f for f in REQUIRED_FIELDS[tool]
        if f not in args or args[f] in (None, "")
    ]
    if missing:
        log.warning(
            "TOOL_MISSING_FIELDS user_id=%s tool=%s missing=%s",
            user_id,
            tool,
            missing,
        )
        return {**state, "tool_call": None}

    try:
        log.info(
            "TOOL_EXEC_START user_id=%s tool=%s args=%s",
            user_id,
            tool,
            args,
        )
        result = TOOL_REGISTRY[tool](**args)
        log.info(
            "TOOL_EXEC_OK user_id=%s tool=%s result=%s",
            user_id,
            tool,
            result,
        )
    except Exception as e:
        log.exception(
            "TOOL_EXEC_FAIL user_id=%s tool=%s error=%s",
            user_id,
            tool,
            str(e),
        )
        return {
            **state,
            "messages": state["messages"] + [{
                "role": "assistant",
                "content": "❌ Action failed safely"
            }],
            "tool_call": None,
        }

    return {
        **state,
        "tool_result": result,
        "tool_call": None,
    }

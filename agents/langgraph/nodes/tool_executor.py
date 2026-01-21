# agents/langgraph/nodes/tool_executor.py

from agents.langgraph.state import AgentState
from agents.langgraph.tools import seller_create_product_tool

# Tool registry
TOOL_REGISTRY = {
    "seller_create_product": seller_create_product_tool,
}

# Required fields per tool
REQUIRED_FIELDS = {
    "seller_create_product": ["name", "price"],
}

def tool_executor(state: AgentState) -> AgentState:
    tool_call = state.get("tool_call")
    if not tool_call:
        return state

    tool_name = tool_call.get("name")

    if tool_name not in TOOL_REGISTRY:
        return {
            **state,
            "messages": state["messages"] + [{
                "role": "assistant",
                "content": f"Unknown tool requested: {tool_name}"
            }],
            "tool_call": None,
        }

    raw_args = tool_call.get("arguments", {})

    # 🔒 HARDENING: LLM arguments may be garbage
    if isinstance(raw_args, dict):
        args = raw_args.copy()
    else:
        args = {}

    # 🔐 Inject trusted values ONLY from backend
    args["seller_id"] = int(state["user_id"])

    # Temporary sane defaults (until LLM asks explicitly)
    args.setdefault("category_id", 2)      # Shoes
    args.setdefault("stock_quantity", 10)

    # ✅ Validate required fields
    missing_fields = [
        field
        for field in REQUIRED_FIELDS.get(tool_name, [])
        if field not in args or args[field] in (None, "")
    ]

    if missing_fields:
        return {
            **state,
            "messages": state["messages"] + [{
                "role": "assistant",
                "content": (
                    "I need the following details to proceed: "
                    + ", ".join(missing_fields)
                )
            }],
            "tool_call": None,
        }

    # 🚀 Execute tool
    tool_fn = TOOL_REGISTRY[tool_name]

    try:
        result = tool_fn(**args)
    except Exception as e:
        return {
            **state,
            "messages": state["messages"] + [{
                "role": "assistant",
                "content": f"Tool execution failed: {str(e)}"
            }],
            "tool_call": None,
        }

    return {
        **state,
        "tool_result": result,
        "tool_call": None,
    }

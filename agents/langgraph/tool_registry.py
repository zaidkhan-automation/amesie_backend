# agents/langgraph/tool_registry.py

from agents.langgraph.tools import (
    seller_create_product_tool,
    seller_update_price_tool,
)

TOOL_REGISTRY = {
    "seller_create_product": seller_create_product_tool,
    "seller_update_price": seller_update_price_tool,
}

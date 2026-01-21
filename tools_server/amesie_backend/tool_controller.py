# agents/tool_controller.py

from typing import Dict, Any
from core.database import SessionLocal

from agents.tools.seller_products import list_seller_products
from agents.tools.seller_create_product import create_product
from agents.tools.seller_update_stock import update_stock
from agents.tools.seller_update_price import update_price
from agents.tools.seller_delete_product import delete_product
from agents.tools.seller_dashboard import get_seller_dashboard


# ==========================================================
# TOOL REGISTRY
# ==========================================================
TOOL_MAP = {
    "list_products": list_seller_products,
    "create_product": create_product,
    "update_stock": update_stock,
    "update_price": update_price,
    "delete_product": delete_product,
    "seller_dashboard": get_seller_dashboard,
}


# ==========================================================
# TOOL EXECUTOR
# ==========================================================
def run_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name not in TOOL_MAP:
        raise ValueError(f"Unknown tool: {tool_name}")

    db = SessionLocal()
    try:
        tool_fn = TOOL_MAP[tool_name]
        return tool_fn(db=db, **arguments)
    finally:
        db.close()

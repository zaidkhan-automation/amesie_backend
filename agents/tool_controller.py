# agents/tool_controller.py

from typing import Dict, Any
from sqlalchemy.orm import Session

from core.database import SessionLocal

# ─────────────────────────────────────────────
# IMPORT TOOLS (SINGLE SOURCE OF TRUTH)
# ─────────────────────────────────────────────
from agents.tools.calculator import run as calculator_run
from agents.tools.report_generator import generate_report
from agents.tools.pdf_exporter import generate_pdf

from agents.tools.seller_create_product import create_product
from agents.tools.seller_products import list_seller_products
from agents.tools.seller_update_price import update_price
from agents.tools.seller_update_stock import update_stock
from agents.tools.seller_delete_product import delete_product
from agents.tools.seller_dashboard import get_seller_dashboard
from agents.tools.seller_add_product_image import add_product_image
from agents.tools.seller_actions import run as seller_actions_run


# ─────────────────────────────────────────────
# TOOL REGISTRY (NAMES MUST MATCH SYSTEM PROMPT)
# ─────────────────────────────────────────────
TOOL_MAP = {
    # utility
    "calculator": calculator_run,
    "report_generator": generate_report,
    "pdf_exporter": generate_pdf,

    # seller core
    "seller_create_product": create_product,
    "seller_products": list_seller_products,
    "seller_update_price": update_price,
    "seller_update_stock": update_stock,
    "seller_delete_product": delete_product,
    "seller_dashboard": get_seller_dashboard,
    "seller_add_product_image": add_product_image,

    # generic
    "seller_actions": seller_actions_run,
}


# ─────────────────────────────────────────────
# TOOL EXECUTOR (DB SAFE)
# ─────────────────────────────────────────────
def run_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name not in TOOL_MAP:
        raise ValueError(f"Unknown tool: {tool_name}")

    tool_fn = TOOL_MAP[tool_name]

    db = SessionLocal()
    try:
        if "db" in tool_fn.__code__.co_varnames:
            return tool_fn(db=db, **arguments)

        return tool_fn(**arguments)
    finally:
        db.close()

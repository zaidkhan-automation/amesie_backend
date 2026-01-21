from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import importlib
import traceback

app = FastAPI(title="Amesie Tools Runtime")

# ─────────────────────────────────────────────
# TOOL REGISTRY (EXPLICIT, NO MAGIC)
# ─────────────────────────────────────────────
TOOL_REGISTRY = {
    "calculator": "agents.tools.calculator",
    "seller_create_product": "agents.tools.seller_create_product",
    "seller_update_price": "agents.tools.seller_update_price",
    "seller_update_stock": "agents.tools.seller_update_stock",
    "seller_delete_product": "agents.tools.seller_delete_product",
    "seller_products": "agents.tools.seller_products",
    "seller_dashboard": "agents.tools.seller_dashboard",
    "dashboard_analysis": "agents.tools.dashboard_analysis",
    "report_generator": "agents.tools.report_generator",
    "pdf_exporter": "agents.tools.pdf_exporter",
}

# ─────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMA
# ─────────────────────────────────────────────
class ToolRequest(BaseModel):
    tool_name: str
    args: Dict[str, Any] = {}

class ToolResponse(BaseModel):
    success: bool
    output: Any = None
    error: str | None = None

# ─────────────────────────────────────────────
# TOOL EXECUTOR
# ─────────────────────────────────────────────
@app.post("/execute", response_model=ToolResponse)
def execute_tool(payload: ToolRequest):
    tool_name = payload.tool_name

    if tool_name not in TOOL_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{tool_name}' not allowed"
        )

    try:
        module_path = TOOL_REGISTRY[tool_name]
        module = importlib.import_module(module_path)

        if not hasattr(module, "run"):
            raise RuntimeError("Tool missing required run() function")

        result = module.run(**payload.args)

        return ToolResponse(
            success=True,
            output=result
        )

    except Exception as e:
        return ToolResponse(
            success=False,
            error=str(e),
        )

# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

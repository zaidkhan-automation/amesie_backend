from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import importlib
import time
import threading
import uuid

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
# SAFETY LIMITS
# ─────────────────────────────────────────────
MAX_EXECUTION_SECONDS = 5  # hard timeout
ACTIVE_EXECUTIONS: set[str] = set()
LOCK = threading.Lock()

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
# INTERNAL SAFE RUNNER
# ─────────────────────────────────────────────
def _run_with_timeout(fn, kwargs, timeout):
    result = {}
    error = {}

    def target():
        try:
            result["value"] = fn(**kwargs)
        except Exception as e:
            error["err"] = str(e)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        raise RuntimeError("Tool execution timed out")

    if error:
        raise RuntimeError(error["err"])

    return result.get("value")

# ─────────────────────────────────────────────
# TOOL EXECUTOR (LOOP-SAFE)
# ─────────────────────────────────────────────
@app.post("/execute", response_model=ToolResponse)
def execute_tool(payload: ToolRequest):
    exec_id = str(uuid.uuid4())

    with LOCK:
        if exec_id in ACTIVE_EXECUTIONS:
            raise HTTPException(status_code=429, detail="Duplicate execution blocked")
        ACTIVE_EXECUTIONS.add(exec_id)

    try:
        tool_name = payload.tool_name

        if tool_name not in TOOL_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{tool_name}' not allowed"
            )

        module_path = TOOL_REGISTRY[tool_name]
        module = importlib.import_module(module_path)

        if not hasattr(module, "run"):
            raise RuntimeError("Tool missing required run() function")

        result = _run_with_timeout(
            fn=module.run,
            kwargs=payload.args,
            timeout=MAX_EXECUTION_SECONDS,
        )

        return ToolResponse(success=True, output=result)

    except Exception as e:
        return ToolResponse(success=False, error=str(e))

    finally:
        with LOCK:
            ACTIVE_EXECUTIONS.discard(exec_id)

# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

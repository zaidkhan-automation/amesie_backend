# agents/tools/seller_actions.py

def run(action: str, payload: dict | None = None):
    return {
        "action": action,
        "payload": payload or {},
        "status": "executed",
    }

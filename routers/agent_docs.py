# routers/agent_docs.py
from fastapi import APIRouter

router = APIRouter(tags=["Agent WebSocket"])

@router.get("/ws/seller/agent")
def seller_agent_ws_docs():
    """
    WebSocket Endpoint (DOCUMENTATION ONLY)

    Connect via:
    ws://<host>/ws/seller/agent

    Handshake payload:
    {
      "token": "<JWT>",
      "chat_id": null
    }
    """
    return {
        "type": "websocket",
        "url": "/ws/seller/agent",
        "note": "Use WebSocket client, not HTTP"
    }

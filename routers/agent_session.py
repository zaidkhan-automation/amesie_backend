import uuid
from fastapi import APIRouter, Depends
from core.auth import get_current_seller
from ws.session_store import ACTIVE_WS_SESSIONS
from core.logger import get_logger
router = APIRouter()
log = get_logger("AGENT_SESSION")


@router.post("/api/agent/session")
def create_agent_session(
    seller_id: int = Depends(get_current_seller)
):
    conversation_id = f"conv_{uuid.uuid4()}"

    ACTIVE_WS_SESSIONS[conversation_id] = seller_id

    log.info(
        "WS_SESSION_CREATED seller_id=%s conversation_id=%s",
        seller_id,
        conversation_id,
    )

    return {
        "conversation_id": conversation_id,
        "ws_url": f"/ws/seller/agent?conversation_id={conversation_id}"
    }

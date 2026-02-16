from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from embeddings.mpnet import embed_texts

router = APIRouter(prefix="/embed", tags=["embeddings"])

class EmbedRequest(BaseModel):
    texts: List[str]

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    dimension: int
    model: str

@router.post(
    "",
    response_model=EmbedResponse,
    include_in_schema=False
)
def embed(req: EmbedRequest):
    embeddings = embed_texts(req.texts)
    return {
        "embeddings": embeddings,
        "dimension": len(embeddings[0]) if embeddings else 0,
        "model": "paraphrase-multilingual-mpnet-base-v2"
    }

@router.get(
    "/health",
    include_in_schema=False
)
def health():
    return {"status": "ok"}

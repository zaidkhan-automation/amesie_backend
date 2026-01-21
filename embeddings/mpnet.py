# embeddings/mpnet.py

from sentence_transformers import SentenceTransformer

_MODEL = None

def get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        )
    return _MODEL


def embed_text(text: str) -> list[float]:
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [embed_text(t) for t in texts]

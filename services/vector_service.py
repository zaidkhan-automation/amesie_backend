from typing import List, Optional
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import logging
import traceback

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vector_service")

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
COLLECTION_NAME = "products_v1"
QDRANT_URL = "http://127.0.0.1:6333"

client = QdrantClient(url=QDRANT_URL)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


# ─────────────────────────────────────────────
# EMBEDDING
# ─────────────────────────────────────────────
def embed_text(text: str) -> List[float]:
    try:
        return model.encode(text or "").tolist()
    except Exception:
        logger.error("Embedding failed")
        logger.error(traceback.format_exc())
        raise


# ─────────────────────────────────────────────
# UPSERT MULTI VECTOR (FIXED + CLEAN)
# ─────────────────────────────────────────────
def upsert_product_vector(product):
    try:
        if not product:
            logger.warning("Product is None, skipping upsert")
            return

        product_id = int(product.id)

        name_text = product.name or ""
        description_text = product.description or ""
        tags_text = f"{product.sku or ''} category_{product.category_id or ''}"

        # Generate vectors explicitly (debuggable)
        name_vec = embed_text(name_text)
        short_desc_vec = embed_text(description_text[:200])
        desc_vec = embed_text(description_text)
        tags_vec = embed_text(tags_text)

        payload = {
            "product_id": product_id,
            "seller_id": product.seller_id,
            "category_id": product.category_id,
            "price": float(product.price or 0),
            "is_active": bool(product.is_active),
            "stock_quantity": int(product.stock_quantity or 0),
            "name": name_text,
            "description": description_text,
        }

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                {
                    "id": product_id,
                    "vector": {
                        "name_vector": name_vec,
                        "short_desc_vector": short_desc_vec,
                        "description_vector": desc_vec,
                        "tags_vector": tags_vec,
                    },
                    "payload": payload,
                }
            ],
        )

        logger.info(f"Vector upserted successfully for product {product_id}")

    except Exception:
        logger.error("Upsert failed")
        logger.error(traceback.format_exc())
        raise


# ─────────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────────
def search_products(
    query: str,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
):
    try:
        logger.info(f"Searching for: {query}")

        query_vector = embed_text(query)

        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            using="description_vector",
            limit=30,
            with_payload=True,
        )

        seen_ids = set()
        results = []

        for point in response.points:
            payload = point.payload or {}
            product_id = payload.get("product_id")

            if not product_id:
                continue

            if product_id in seen_ids:
                continue
            seen_ids.add(product_id)

            if not payload.get("is_active", False):
                continue

            if payload.get("stock_quantity", 0) <= 0:
                continue

            if category_id and payload.get("category_id") != category_id:
                continue

            price = float(payload.get("price", 0))

            if min_price is not None and price < min_price:
                continue

            if max_price is not None and price > max_price:
                continue

            results.append({
                "id": product_id,
                "name": payload.get("name"),
                "description": payload.get("description"),
                "price": price,
                "score": round(point.score, 4),
                "product_url": f"/product/{product_id}",
            })

            if len(results) >= 10:
                break

        logger.info(f"Final filtered results: {len(results)}")

        return results

    except Exception:
        logger.error("Search failed")
        logger.error(traceback.format_exc())
        raise

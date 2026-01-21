from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

QDRANT_URL = "http://localhost:6333"
VECTOR_SIZE = 768

client = QdrantClient(url=QDRANT_URL)

collections = [
    "chat_memory",
    "chat_summary",
    "facts",
]

for name in collections:
    if client.collection_exists(name):
        print(f"✅ Collection already exists: {name}")
        continue

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )
    print(f"🆕 Created collection: {name}")

print("\n🎉 Qdrant Step-1 complete.")

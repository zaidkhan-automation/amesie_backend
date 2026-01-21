from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient(url="http://localhost:6333")

client.recreate_collection(
    collection_name="user_facts",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)

print("✅ Qdrant collection 'user_facts' created successfully.")

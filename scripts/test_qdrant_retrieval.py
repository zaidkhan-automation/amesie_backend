from embeddings.mpnet import embed_text
from vectorstore.qdrant_reader import retrieve_chat_context
from llm.context_builder import build_llm_prompt

CHAT_ID = "test_chat_001"

user_message = "What was my business idea again?"

embedding = embed_text(user_message)

context = retrieve_chat_context(
    chat_id=CHAT_ID,
    embedding=embedding,
    top_k=4,
)

prompt = build_llm_prompt(
    retrieved_context=context,
    user_message=user_message,
)

print("\n--- FINAL PROMPT ---\n")
print(prompt)

from agents.langgraph.graph import agent_app

state = {
    "chat_id": "test_chat_1",
    "user_id": 1,
    "messages": [
        {"role": "user", "content": "please create product"}
    ],
    "tool_call": {
        "name": "seller_create_product",
        "arguments": {
            "seller_id": 1,
            "name": "Test Shoe",
            "price": 999,
            "stock_quantity": 10,
            "category_id": 2
        }
    },
    "tool_result": None,
    "memory_context": []
}

out = agent_app.invoke(state)
print(out)

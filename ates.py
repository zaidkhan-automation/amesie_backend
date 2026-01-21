from agents.langgraph.tools import seller_create_product_tool

print(
    seller_create_product_tool(
        user_id=1,
        name="Test Shoe",
        price=999,
        stock_quantity=10,
    )
)

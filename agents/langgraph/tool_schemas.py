SELLER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "seller_create_product",
            "description": "Create a new product for the seller",
            "parameters": {
                "type": "object",
                "required": ["name", "price"],
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Product name"
                    },
                    "price": {
                        "type": "number",
                        "description": "Product price"
                    },
                    "stock_quantity": {
                        "type": "integer",
                        "description": "Available stock"
                    }
                }
            }
        }
    }
]

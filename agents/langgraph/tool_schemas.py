SELLER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "seller_create_product",
            "description": "Create a new product",
            "parameters": {
                "type": "object",
                "required": ["name", "price"],
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                    "stock_quantity": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seller_update_price",
            "description": "Update product price",
            "parameters": {
                "type": "object",
                "required": ["product_id", "new_price"],
                "properties": {
                    "product_id": {"type": "integer"},
                    "new_price": {"type": "number"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seller_update_stock",
            "description": "Update product stock",
            "parameters": {
                "type": "object",
                "required": ["product_id", "stock_quantity"],
                "properties": {
                    "product_id": {"type": "integer"},
                    "stock_quantity": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seller_delete_product",
            "description": "Delete a product",
            "parameters": {
                "type": "object",
                "required": ["product_id"],
                "properties": {
                    "product_id": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seller_list_products",
            "description": "List all products",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Safely evaluate a mathematical expression",
            "parameters": {
                "type": "object",
                "required": ["expression"],
                 "properties": {
                    "expression": {
                        "type": "string",
                        "description":"Example 2+3*4" 
                    },
 
                },
            },
        },
    },
]

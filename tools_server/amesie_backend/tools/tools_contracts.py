TOOL_CONTRACTS = {
    "calculator": {
        "description": "Perform basic arithmetic operations",
        "inputs": {
            "operation": ["add", "subtract", "multiply", "divide"],
            "a": "number",
            "b": "number"
        },
        "output": "number"
    },

    "dashboard_analysis": {
        "description": "Analyze seller dashboard stats and produce insights",
        "inputs": {
            "total_products": "int",
            "total_orders": "int",
            "pending_orders": "int",
            "low_stock_products": "int"
        },
        "output": "text_summary"
    },

    "text_to_pdf": {
        "description": "Convert text report into PDF",
        "inputs": {
            "text": "string",
            "filename": "string"
        },
        "output": "file_path"
    }
}

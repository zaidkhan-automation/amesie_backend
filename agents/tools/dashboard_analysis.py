def analyze_dashboard(stats: dict):
    insights = []

    if stats.get("low_stock_products", 0) > 0:
        insights.append("Some products are running low on stock.")

    if stats.get("pending_orders", 0) > 5:
        insights.append("High number of pending orders. Consider faster fulfillment.")

    if stats.get("total_products", 0) == 0:
        insights.append("No products found. Add products to start selling.")

    if not insights:
        insights.append("Dashboard looks healthy.")

    return {
        "summary": insights,
        "raw_stats": stats
    }
def run():
    return {
        "summary": [
            "Some products are running low on stock",
            "Pending orders detected"
        ],
        "raw_stats": {
            "total_products": 12,
            "total_orders": 58,
            "pending_orders": 9,
            "low_stock_products": 3
        }
    }

from sqlalchemy.orm import Session
from db.models import Product, Order, OrderItem

LOW_STOCK_THRESHOLD = 10

def get_seller_dashboard(seller_id: int, db: Session):
    # Total products
    total_products = (
        db.query(Product)
        .filter(
            Product.seller_id == seller_id,
            Product.is_deleted == False,
        )
        .count()
    )

    # Total orders (distinct orders containing seller's products)
    total_orders = (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(Product.seller_id == seller_id)
        .distinct()
        .count()
    )

    # Pending orders
    pending_orders = (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(
            Product.seller_id == seller_id,
            Order.order_status == "pending",
        )
        .distinct()
        .count()
    )

    # Low stock products
    low_stock_products = (
        db.query(Product)
        .filter(
            Product.seller_id == seller_id,
            Product.stock_quantity < LOW_STOCK_THRESHOLD,
            Product.is_deleted == False,
        )
        .count()
    )

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "low_stock_products": low_stock_products,
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
    }

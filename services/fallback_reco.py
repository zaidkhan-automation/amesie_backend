from sqlalchemy import text

def get_fallback_recommendations(db, product_id: int, limit: int):
    sql = text("""
        SELECT id AS pid, name, price, 0.5 AS weight
        FROM products
        WHERE is_active = true
          AND is_deleted = false
          AND id != :pid
        ORDER BY created_at DESC
        LIMIT :limit
    """)

    rows = db.execute(sql, {"pid": product_id, "limit": limit}).fetchall()

    return [
        {
            "pid": r.pid,
            "name": r.name,
            "price": r.price,
            "weight": r.weight,
        }
        for r in rows
    ]

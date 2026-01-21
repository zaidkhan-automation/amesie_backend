from psycopg2.extras import RealDictCursor
from core.logging_config import get_logger

logger = get_logger("graph")

def get_similar_products(db, product_id: int, limit: int = 5):
    logger.info(
        f"[GRAPH] Fetching recommendations | product_id={product_id}, limit={limit}"
    )

    try:
        # 🔥 MUST disable prepared statements
        raw_conn = db.get_bind().raw_connection()
        raw_conn.autocommit = True

        cur = raw_conn.cursor(cursor_factory=RealDictCursor)

        # REQUIRED for Apache AGE
        cur.execute('SET search_path = ag_catalog, "$user", public;')

        sql = f"""
        SELECT
            pid,
            name,
            price,
            weight
        FROM cypher(
            'amesie_graph',
            $$
                MATCH (a:Product {{pid: {product_id}}})-[r:SIMILAR]->(b:Product)
                RETURN
                    b.pid    AS pid,
                    b.name   AS name,
                    b.price  AS price,
                    r.weight AS weight
                ORDER BY r.weight DESC
                LIMIT {limit}
            $$
        ) AS (
            pid int,
            name text,
            price float,
            weight float
        );
        """

        cur.execute(sql)
        rows = cur.fetchall()

        cur.close()
        raw_conn.close()

        logger.info(f"[GRAPH] Found {len(rows)} recommendations")
        return rows

    except Exception:
        logger.exception("[GRAPH] FAILED to fetch recommendations")
        return []

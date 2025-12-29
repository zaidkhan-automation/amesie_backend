from psycopg2.extras import RealDictCursor
from core.logging_config import get_logger
from core.database import SessionLocal

logger = get_logger("graph_ingest")


def ingest_bought_with():
    logger.info("========== BOUGHT_WITH INGEST START ==========")

    db = SessionLocal()

    try:
        raw_conn = db.get_bind().raw_connection()
        raw_conn.autocommit = True
        cur = raw_conn.cursor(cursor_factory=RealDictCursor)

        # REQUIRED FOR AGE
        cur.execute('SET search_path = ag_catalog, "$user", public;')

        # ─────────────────────────────────────
        # STEP 1: FETCH CO-PURCHASE PAIRS (SQL)
        # ─────────────────────────────────────
        cur.execute("""
            SELECT
                oi1.product_id AS src,
                oi2.product_id AS dst,
                COUNT(*)       AS freq
            FROM order_items oi1
            JOIN order_items oi2
              ON oi1.order_id = oi2.order_id
             AND oi1.product_id <> oi2.product_id
            GROUP BY oi1.product_id, oi2.product_id
        """)

        pairs = cur.fetchall()
        logger.info(f"[INGEST] Found {len(pairs)} co-purchase pairs")

        # ─────────────────────────────────────
        # STEP 2: WRITE VIA CTE (CRITICAL)
        # ─────────────────────────────────────
        for row in pairs:
            src = row["src"]
            dst = row["dst"]
            freq = row["freq"]

            sql = f"""
            WITH cypher_write AS (
                SELECT *
                FROM cypher(
                    'amesie_graph',
                    $$
                        MATCH (a:Product {{pid: {src}}})
                        MATCH (b:Product {{pid: {dst}}})
                        MERGE (a)-[r:BOUGHT_WITH]->(b)
                        SET r.weight = coalesce(r.weight, 0) + {freq}
                        RETURN a.pid, b.pid, r.weight
                    $$
                ) AS (src int, dst int, weight int)
            )
            SELECT 1;
            """

            cur.execute(sql)
            logger.info(f"[EDGE] {src} → {dst} (+{freq})")

        cur.close()
        raw_conn.close()
        logger.info("========== BOUGHT_WITH INGEST END ==========")

    except Exception:
        logger.exception("[INGEST] BOUGHT_WITH FAILED")

    finally:
        db.close()


if __name__ == "__main__":
    ingest_bought_with()

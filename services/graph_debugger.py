from psycopg2.extras import RealDictCursor
from core.logging_config import get_logger

logger = get_logger("graph_debugger")

def run_graph_debugger(db, product_id: int = 13):
    logger.info("========== GRAPH DEBUGGER START ==========")

    conn = db.connection().connection
    cur = conn.cursor(cursor_factory=RealDictCursor)

    def step(name, sql):
        try:
            logger.info(f"[STEP] {name}")
            cur.execute(sql)
            rows = cur.fetchall() if cur.description else []
            logger.info(f"[PASS] {name} | rows={len(rows)}")
            return rows
        except Exception as e:
            logger.error(f"[FAIL] {name}")
            logger.exception(e)
            return None

    # 1️⃣ search_path
    step(
        "SET search_path",
        'SET search_path = ag_catalog, "$user", public;'
    )

    # 2️⃣ AGE extension
    step(
        "AGE extension check",
        "SELECT * FROM pg_extension WHERE extname = 'age';"
    )

    # 3️⃣ Graph exists
    step(
        "Graph exists",
        "SELECT * FROM ag_catalog.ag_graph WHERE name = 'amesie_graph';"
    )

    # 4️⃣ Simple cypher sanity
    step(
        "Simple cypher test",
        """
        SELECT *
        FROM cypher('amesie_graph', $$ MATCH (n) RETURN count(n) $$)
        AS (cnt bigint);
        """
    )

    # 5️⃣ Product node exists
    step(
        "Product node exists",
        f"""
        SELECT *
        FROM cypher('amesie_graph', $$
            MATCH (p:Product {{pid: {product_id}}})
            RETURN p.pid, p.name
        $$) AS (pid int, name text);
        """
    )

    # 6️⃣ SIMILAR edges exist
    step(
        "SIMILAR edges count",
        """
        SELECT *
        FROM cypher('amesie_graph', $$
            MATCH ()-[r:SIMILAR]->()
            RETURN count(r)
        $$) AS (cnt bigint);
        """
    )

    # 7️⃣ Final recommendation query
    step(
        "FINAL recommendation query",
        f"""
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
                LIMIT 5
            $$
        ) AS (
            pid int,
            name text,
            price float,
            weight float
        );
        """
    )

    cur.close()
    logger.info("========== GRAPH DEBUGGER END ==========")

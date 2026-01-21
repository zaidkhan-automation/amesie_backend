from psycopg2.extras import RealDictCursor
from core.logging_config import get_logger
from geo_routing.db.postgis import get_db

logger = get_logger("geo-routing")

def snap_to_nearest_node(db, lng: float, lat: float) -> int:
    """
    Returns the nearest node ID to the given lat/lng.
    """
    try:
        raw_conn = db.get_bind().raw_connection()
        raw_conn.autocommit = True
        cur = raw_conn.cursor(cursor_factory=RealDictCursor)

        sql = """
        SELECT id
        FROM geo_nodes
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        LIMIT 1;
        """

        cur.execute(sql, (lng, lat))
        row = cur.fetchone()
        cur.close()
        raw_conn.close()

        if row:
            return row["id"]

    except Exception:
        logger.exception(f"[ROUTE] Failed snapping lat={lat}, lng={lng}")

    return None


def compute_shortest_path(db, source_node: int, target_node: int):
    """
    Executes the pgRouting Dijkstra query.
    Returns list of segments with geometry.
    """
    try:
        raw_conn = db.get_bind().raw_connection()
        raw_conn.autocommit = True
        cur = raw_conn.cursor(cursor_factory=RealDictCursor)

        sql = """
        SELECT
          dj.seq,
          dj.node,
          dj.edge,
          dj.cost,
          ST_AsGeoJSON(e.geom) AS geom
        FROM pgr_dijkstra(
          '
          SELECT id, source, target, cost, reverse_cost
          FROM geo_edges
          ',
          %s, %s, directed := false
        ) AS dj
        JOIN geo_edges e ON dj.edge = e.id;
        """

        cur.execute(sql, (source_node, target_node))
        rows = cur.fetchall()
        cur.close()
        raw_conn.close()
        return rows

    except Exception:
        logger.exception(
            f"[ROUTE] Failed to compute shortest path from {source_node} to {target_node}"
        )
        return []

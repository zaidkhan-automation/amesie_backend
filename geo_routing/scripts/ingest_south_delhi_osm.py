import logging
import os
import osmnx as ox
from psycopg2.extras import RealDictCursor
from geo_routing.db.postgis import SessionLocal

# Basic logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("osm-ingest")

# South Delhi bounding box
BOUNDING_BOX = {
    "north": 28.60,
    "south": 28.45,
    "east": 77.30,
    "west": 77.15,
}

def create_tables_and_indexes(raw_conn):
    """
    Create tables and spatial indexes if they do not exist.
    """
    cur = raw_conn.cursor()
    # Create nodes table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS geo_nodes (
        id SERIAL PRIMARY KEY,
        geom GEOMETRY(Point, 4326)
    );
    """)

    # Create edges table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS geo_edges (
        id SERIAL PRIMARY KEY,
        source INTEGER,
        target INTEGER,
        cost DOUBLE PRECISION,
        reverse_cost DOUBLE PRECISION,
        geom GEOMETRY(LineString, 4326)
    );
    """)

    # Spatial indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_geo_nodes_geom ON geo_nodes USING GIST(geom);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_geo_edges_geom ON geo_edges USING GIST(geom);")

    # Index source and target to speed up pgRouting
    cur.execute("CREATE INDEX IF NOT EXISTS idx_geo_edges_source ON geo_edges(source);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_geo_edges_target ON geo_edges(target);")

    raw_conn.commit()
    cur.close()
    logger.info("Tables and indexes created or confirmed existing.")


def ingest_osm():
    """
    Ingest the South Delhi OSM driving road network into PostGIS.
    """
    logger.info("[OSM] Starting download of South Delhi road network...")

    # Download only driving roads
    G = ox.graph_from_bbox(
        bbox=(BOUNDING_BOX["west"], BOUNDING_BOX["south"], BOUNDING_BOX["east"], BOUNDING_BOX["north"]),
        network_type="drive"
    )

    # Convert graph to GeoDataFrames
    nodes, edges = ox.graph_to_gdfs(G)

    logger.info(f"[OSM] Retrieved {len(nodes)} nodes and {len(edges)} edges from OSM.")
    logger.info(f"[DEBUG] Edge columns: {list(edges.columns)}")
    if len(edges) > 0:
        logger.info(f"[DEBUG] Example edge row: {edges.iloc[0].to_dict()}")

    db = SessionLocal()
    raw_conn = db.get_bind().raw_connection()
    raw_conn.autocommit = True

    # Create tables + indexes
    create_tables_and_indexes(raw_conn)

    cur = raw_conn.cursor(cursor_factory=RealDictCursor)
    node_id_map = {}

    # Insert nodes
    for osm_node_id, row in nodes.iterrows():
        lon = float(row["x"])
        lat = float(row["y"])
        cur.execute(
            """
            INSERT INTO geo_nodes (geom)
            VALUES (ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            RETURNING id;
            """,
            (lon, lat),
        )
        db_id = cur.fetchone()["id"]
        node_id_map[osm_node_id] = db_id

    logger.info(f"[OSM] Inserted {len(node_id_map)} nodes into geo_nodes.")

    # Insert edges safely
    count_skipped = 0
    count_inserted = 0
    for idx, row in edges.iterrows():
        # Determine source + target
        if isinstance(idx, tuple) and len(idx) >= 2:
            u = idx[0]
            v = idx[1]
        else:
            if "u" in row.index and "v" in row.index:
                u = row["u"]
                v = row["v"]
            elif "from" in row.index and "to" in row.index:
                u = row["from"]
                v = row["to"]
            else:
                logger.warning(f"[OSM] Unable to find source/target for idx={repr(idx)}")
                count_skipped += 1
                continue

        # Geometry check
        geom = row.get("geometry")
        if geom is None:
            count_skipped += 1
            logger.warning(f"[OSM] Missing geometry for idx={repr(idx)}; skipping.")
            continue
        geom_wkt = geom.wkt

        # Length (meters) or fallback
        length = row.get("length")
        if length is None:
            try:
                length = float(geom.length)
            except Exception:
                length = 0.0

        src_node = node_id_map.get(u)
        tgt_node = node_id_map.get(v)
        if src_node is None or tgt_node is None:
            count_skipped += 1
            continue

        cur.execute(
            """
            INSERT INTO geo_edges (source, target, cost, reverse_cost, geom)
            VALUES (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromText(%s), 4326));
            """,
            (src_node, tgt_node, float(length), float(length), geom_wkt),
        )
        count_inserted += 1

    raw_conn.commit()
    cur.close()
    raw_conn.close()
    db.close()

    logger.info(f"[OSM] Inserted {count_inserted} edges into geo_edges, skipped {count_skipped} rows.")
    logger.info("[OSM] Ingestion complete!")


if __name__ == "__main__":
    ingest_osm()

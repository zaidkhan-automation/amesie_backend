import logging
from geo_routing.db.postgis import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("poi-setup")


def create_poi_tables():
    db = SessionLocal()
    raw_conn = db.get_bind().raw_connection()
    raw_conn.autocommit = True
    cur = raw_conn.cursor()

    logger.info("[POI] Creating geo_pois table...")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS geo_pois (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        poi_type TEXT NOT NULL, -- restaurant, buyer, warehouse, driver
        geom GEOMETRY(Point, 4326) NOT NULL,
        nearest_node INTEGER,
        metadata JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)

    logger.info("[POI] Creating indexes...")

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_geo_pois_geom
    ON geo_pois USING GIST (geom);
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_geo_pois_type
    ON geo_pois (poi_type);
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_geo_pois_nearest_node
    ON geo_pois (nearest_node);
    """)

    raw_conn.commit()
    cur.close()
    raw_conn.close()
    db.close()

    logger.info("[POI] Table and indexes ready.")


if __name__ == "__main__":
    create_poi_tables()

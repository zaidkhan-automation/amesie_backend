import logging
from sqlalchemy import text
from geo_routing.db.postgis import engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("poi-migration")

DDL_STATEMENTS = [
    """
    ALTER TABLE geo_pois
    ADD COLUMN IF NOT EXISTS nearest_node INTEGER;
    """,
    """
    ALTER TABLE geo_pois
    ADD COLUMN IF NOT EXISTS source TEXT;
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_geo_pois_geom
    ON geo_pois USING GIST (geom);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_geo_pois_nearest
    ON geo_pois (nearest_node);
    """
]

def run_migration():
    logger.info("[POI] Starting geo_pois schema migration...")

    with engine.begin() as conn:
        for stmt in DDL_STATEMENTS:
            conn.execute(text(stmt))

    logger.info("[POI] geo_pois schema is up to date ✅")

if __name__ == "__main__":
    run_migration()

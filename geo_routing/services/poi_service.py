from psycopg2.extras import RealDictCursor
from geo_routing.db.postgis import SessionLocal


def create_poi(name, poi_type, lat, lon, metadata=None):
    db = SessionLocal()
    raw_conn = db.get_bind().raw_connection()
    raw_conn.autocommit = True
    cur = raw_conn.cursor(cursor_factory=RealDictCursor)

    # Snap POI to nearest road node
    cur.execute("""
        SELECT id
        FROM geo_nodes
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        LIMIT 1;
    """, (lon, lat))
    nearest_node = cur.fetchone()["id"]

    cur.execute("""
        INSERT INTO geo_pois (name, poi_type, geom, nearest_node, metadata)
        VALUES (
            %s,
            %s,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326),
            %s,
            %s
        )
        RETURNING
            id,
            name,
            poi_type,
            nearest_node,
            ST_AsGeoJSON(geom) AS geometry;
    """, (name, poi_type, lon, lat, nearest_node, metadata or {}))

    poi = cur.fetchone()

    cur.close()
    raw_conn.close()
    db.close()
    return poi


def list_pois():
    db = SessionLocal()
    raw_conn = db.get_bind().raw_connection()
    cur = raw_conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            id,
            name,
            poi_type,
            nearest_node,
            ST_AsGeoJSON(geom) AS geometry
        FROM geo_pois;
    """)

    rows = cur.fetchall()

    cur.close()
    raw_conn.close()
    db.close()
    return rows


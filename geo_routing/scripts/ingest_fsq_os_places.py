import duckdb
from geo_routing.db.postgis import SessionLocal
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fsq-poi-ingest")

# South Delhi bounding box
BBOX = {
    "west": 77.15,
    "south": 28.45,
    "east": 77.30,
    "north": 28.60,
}

# Public FSQ OS Places S3 path (NO credentials required)
FSQ_PARQUET = (
    "s3://fsq-os-places-us-east-1/"
    "release/dt=2024-11-19/places/parquet/*.parquet"
)

def ingest_pois():
    logger.info("[FSQ] Querying Foursquare OS Places from S3 via DuckDB")

    query = f"""
    SELECT
        fsq_place_id,
        name,
        latitude  AS lat,
        longitude AS lon
    FROM '{FSQ_PARQUET}'
    WHERE latitude BETWEEN {BBOX["south"]} AND {BBOX["north"]}
      AND longitude BETWEEN {BBOX["west"]} AND {BBOX["east"]}
      AND name IS NOT NULL
    """

    df = duckdb.query(query).to_df()
    logger.info(f"[FSQ] Retrieved {len(df)} POIs for South Delhi")

    db = SessionLocal()
    raw_conn = db.get_bind().raw_connection()
    raw_conn.autocommit = True
    cur = raw_conn.cursor(cursor_factory=RealDictCursor)

    # Cache road nodes for snapping
    cur.execute("""
        SELECT id, ST_X(geom) AS lon, ST_Y(geom) AS lat
        FROM geo_nodes
    """)
    nodes = cur.fetchall()

    def nearest_node(lat, lon):
        best_id = None
        best_dist = float("inf")
        for n in nodes:
            d = (lat - n["lat"])**2 + (lon - n["lon"])**2
            if d < best_dist:
                best_dist = d
                best_id = n["id"]
        return best_id

    inserted = 0

    for row in df.itertuples(index=False):
        nn = nearest_node(row.lat, row.lon)
        if nn is None:
            continue

        cur.execute(
            """
            INSERT INTO geo_pois
                (name, poi_type, geom, nearest_node, source)
            VALUES
                (%s, %s,
                 ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                 %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                row.name,
                "fsq_os_place",
                row.lon,
                row.lat,
                nn,
                "foursquare_os_places",
            ),
        )
        inserted += 1

    raw_conn.commit()
    cur.close()
    raw_conn.close()
    db.close()

    logger.info(f"[FSQ] Inserted {inserted} POIs into geo_pois")

if __name__ == "__main__":
    ingest_pois()

from sqlalchemy import text
from sqlalchemy.orm import Session

def create_schema(db: Session):
    queries = [
        """
        CREATE EXTENSION IF NOT EXISTS postgis;
        """,
        """
        CREATE EXTENSION IF NOT EXISTS pgrouting;
        """,
        """
        CREATE TABLE IF NOT EXISTS road_nodes (
            id SERIAL PRIMARY KEY,
            geom GEOMETRY(Point, 4326)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS road_edges (
            id SERIAL PRIMARY KEY,
            source INTEGER,
            target INTEGER,
            cost DOUBLE PRECISION,
            geom GEOMETRY(LineString, 4326)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS buyers (
            id SERIAL PRIMARY KEY,
            geom GEOMETRY(Point, 4326),
            nearest_node INTEGER
        );
        """
    ]

    for q in queries:
        db.execute(text(q))

    db.commit()

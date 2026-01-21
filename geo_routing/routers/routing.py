from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from geo_routing.db.postgis import get_db
from geo_routing.services.routing_service import compute_shortest_path, snap_to_nearest_node
router = APIRouter(prefix="/geo-routing", tags=["Geo Routing"])

@router.post("/route")
def route_by_coordinates(
    start: dict,
    end: dict,
    db: Session = Depends(get_db)
):
    """
    Expects JSON:
    {
      "start": {"lat": float, "lng": float},
      "end":   {"lat": float, "lng": float}
    }
    """

    # Validate input
    if "lat" not in start or "lng" not in start:
        raise HTTPException(status_code=400, detail="Invalid start coordinates")
    if "lat" not in end or "lng" not in end:
        raise HTTPException(status_code=400, detail="Invalid end coordinates")

    # Snap to nearest nodes
    source_node = snap_to_nearest_node(db, start["lng"], start["lat"])
    target_node = snap_to_nearest_node(db, end["lng"], end["lat"])

    if not source_node or not target_node:
        raise HTTPException(status_code=400, detail="Unable to snap points to graph nodes")

    # Compute shortest path
    segments = compute_shortest_path(db, source_node, target_node)
    if not segments:
        raise HTTPException(status_code=500, detail="Routing computation failed")

    # Build a combined list of coordinates for frontends
    route_coords = []
    for seg in segments:
        try:
            geom_json = seg["geom"]
            route_coords.append(geom_json)
        except KeyError:
            continue

    return {
        "source_node": source_node,
        "target_node": target_node,
        "total_segments": len(segments),
        "segments": segments,
        "geometry": route_coords
    }

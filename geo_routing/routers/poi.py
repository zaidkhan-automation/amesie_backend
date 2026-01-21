from fastapi import APIRouter
from geo_routing.services.poi_service import create_poi, list_pois

router = APIRouter(prefix="/poi", tags=["POI"])



@router.post("/add_poi")
def add_poi(
    name: str,
    poi_type: str,
    lat: float,
    lon: float
):
    return create_poi(name, poi_type, lat, lon)


@router.get("/get_all")
def get_all_pois():
    return list_pois()

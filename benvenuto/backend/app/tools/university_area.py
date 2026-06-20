"""Tool 7 — practical info about the area around an Italian university."""
from app.services.osm import geocode, nearby

DEFAULT = ["supermarket", "pharmacy", "bank", "cafe", "subway_entrance", "bus_station"]


async def university_area(university: str, categories: list[str] | None = None) -> dict:
    coords = await geocode(university)
    if not coords:
        return {"error": f"Couldn't locate '{university}'. Try a fuller name plus city."}
    lat, lon = coords
    places = await nearby(lat, lon, categories or DEFAULT, radius_m=1200)
    return {
        "university": university,
        "center": {"lat": lat, "lon": lon},
        "places": places[:25],
        "map_hint": f"https://www.openstreetmap.org/#map=16/{lat}/{lon}",
    }

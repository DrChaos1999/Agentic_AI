"""OpenStreetMap helpers: Nominatim (geocode) + Overpass (nearby amenities).

Free, no key. Nominatim REQUIRES a real User-Agent and asks for <=1 req/sec,
so we cache geocodes in-process.
"""
import asyncio
import httpx
from app.config import settings

HEADERS = {"User-Agent": settings.OSM_USER_AGENT}
_geocode_cache: dict[str, tuple[float, float] | None] = {}


async def geocode(place: str) -> tuple[float, float] | None:
    key = place.strip().lower()
    if key in _geocode_cache:
        return _geocode_cache[key]
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1, "countrycodes": "it"}
    async with httpx.AsyncClient(headers=HEADERS, timeout=20) as c:
        r = await c.get(url, params=params)
        data = r.json()
    result = (float(data[0]["lat"]), float(data[0]["lon"])) if data else None
    _geocode_cache[key] = result
    await asyncio.sleep(1)  # be polite to Nominatim
    return result


async def nearby(lat: float, lon: float, amenities: list[str],
                 radius_m: int = 1000) -> list[dict]:
    filters = "".join(
        f'node["amenity"="{a}"](around:{radius_m},{lat},{lon});'
        f'node["shop"="{a}"](around:{radius_m},{lat},{lon});'
        for a in amenities
    )
    q = f"[out:json][timeout:25];({filters});out body 40;"
    async with httpx.AsyncClient(headers=HEADERS, timeout=40) as c:
        r = await c.post("https://overpass-api.de/api/interpreter", data=q)
    elements = r.json().get("elements", [])
    seen, out = set(), []
    for e in elements:
        tags = e.get("tags", {})
        name = tags.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        out.append({
            "name": name,
            "kind": tags.get("amenity") or tags.get("shop"),
            "lat": e.get("lat"), "lon": e.get("lon"),
        })
    return out

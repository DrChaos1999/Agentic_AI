"""Tool 6 — where to buy a specific item/ingredient near a location."""
from app.services.osm import geocode, nearby
from app.services.websearch import web_search
from app.llm import summarize
from app.config import settings

SHOP_TYPES = ["supermarket", "greengrocer", "convenience", "marketplace", "deli"]


async def grocery_finder(item: str, location: str) -> dict:
    coords = await geocode(location)
    shops = []
    if coords:
        shops = await nearby(coords[0], coords[1], SHOP_TYPES, radius_m=1500)

    web = []
    if settings.ENABLE_WEB_SEARCH:
        web = await web_search(f"where to buy {item} in {location} Italy shop")

    context = (
        "Nearby shops: " + ", ".join(s["name"] for s in shops[:15]) +
        "\n\nWeb results:\n" + "\n".join(f"- {w['title']}: {w['snippet']}" for w in web)
    )
    brief = await summarize(
        f"Advise where to buy '{item}' near {location}. Point to the most likely nearby "
        "shops, and mention any specialty/ethnic/international grocers from the web "
        "results that would stock it.",
        context,
    )
    return {
        "item": item, "location": location,
        "shops": shops[:15], "brief": brief,
        "map_hint": (f"https://www.openstreetmap.org/#map=15/{coords[0]}/{coords[1]}"
                     if coords else None),
    }

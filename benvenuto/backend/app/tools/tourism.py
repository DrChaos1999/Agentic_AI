"""Tool 4 — top spots in a region PLUS the scams/traps to avoid."""
import httpx
from app.rag.store import rag_query
from app.services.websearch import web_search
from app.llm import summarize
from app.config import settings


async def _wikivoyage(place: str) -> str:
    url = "https://en.wikivoyage.org/w/api.php"
    params = {
        "action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1,
        "redirects": 1, "titles": place, "format": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(url, params=params,
                            headers={"User-Agent": settings.OSM_USER_AGENT})
        pages = r.json().get("query", {}).get("pages", {})
        return " ".join(p.get("extract", "") for p in pages.values())[:3000]
    except Exception:
        return ""


async def tourism_guide(region: str, interests: str | None = None) -> dict:
    wv = await _wikivoyage(region)
    traps = await rag_query("tourism_traps", f"{region} scams tourist traps", k=4)

    web = []
    if settings.ENABLE_WEB_SEARCH:
        web = await web_search(f"{region} Italy common tourist scams to avoid")

    context = "\n\n".join(
        [f"Overview: {wv}"] + traps + [w["snippet"] for w in web]
    )
    brief = await summarize(
        "Write two sections. (1) 'Top spots' - the best places to see in the region, "
        "tuned to the stated interests if any. (2) 'Traps to avoid' - specific, concrete "
        "scams and overcharging tricks with how to dodge them. Keep it practical.",
        context + (f"\n\nInterests: {interests}" if interests else ""),
    )
    return {"region": region, "interests": interests, "brief": brief}

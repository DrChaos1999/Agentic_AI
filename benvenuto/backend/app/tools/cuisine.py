"""Tool 3 — regional Italian cuisine, food etiquette, ordering tips."""
from app.rag.store import rag_query
from app.services.websearch import web_search
from app.llm import summarize
from app.config import settings


async def cuisine_guide(query: str, region: str | None = None) -> dict:
    q = f"{query} {region or ''}".strip()
    docs = await rag_query("cuisine", q, k=4)

    web = []
    if settings.ENABLE_WEB_SEARCH and len("".join(docs)) < 300:
        web = await web_search(f"Italian cuisine {region or ''} {query} traditional dishes")

    context = "\n\n".join(docs + [w["snippet"] for w in web])
    brief = await summarize(
        "Explain the regional dishes and food etiquette relevant to the student's "
        "question. Include what to eat, what to avoid (and when - e.g. cappuccino after "
        "noon), and one or two ordering tips. Be specific to the region if one is given.",
        context,
    )
    return {"query": query, "region": region, "brief": brief}

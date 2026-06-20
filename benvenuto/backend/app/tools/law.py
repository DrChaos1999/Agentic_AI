"""Tool 1 — Italian laws & official procedures for a situation."""
from app.rag.store import rag_query
from app.services.websearch import web_search
from app.llm import summarize
from app.config import settings


async def law_info(topic: str, region: str | None = None) -> dict:
    q = f"{topic} {region or ''}".strip()
    docs = await rag_query("law", q, k=4)

    web = []
    if settings.ENABLE_WEB_SEARCH and len("".join(docs)) < 400:
        web = await web_search(f"Italy {q} rules for foreign students official")

    context = "\n\n".join(docs + [w["snippet"] for w in web])
    brief = await summarize(
        "Summarize the Italian rules for the student's situation in 4-6 bullet points. "
        "Be precise about numbers and limits. End with a one-line reminder to verify "
        "with the official authority. Do NOT invent specifics.",
        context,
    )
    return {
        "topic": topic,
        "region": region,
        "brief": brief,
        "sources": [{"type": "kb"} for _ in docs] + [{"type": "web", **w} for w in web],
        "disclaimer": "Informational only - not legal advice. "
                      "Verify with the Questura / Prefettura.",
    }

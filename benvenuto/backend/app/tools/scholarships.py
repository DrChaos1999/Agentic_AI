"""Tool 8 — scholarships & internships for international students at a university."""
from app.rag.store import rag_query
from app.services.websearch import web_search
from app.llm import summarize
from app.config import settings


async def scholarships(university: str, field: str | None = None) -> dict:
    q = f"{university} {field or ''} international students scholarships internships"
    docs = await rag_query("scholarships", q, k=4)

    web = []
    if settings.ENABLE_WEB_SEARCH:
        web = await web_search(
            f"{university} scholarships internships international students {field or ''}"
        )

    context = "\n\n".join(docs + [f"{w['title']}: {w['snippet']} ({w['url']})" for w in web])
    brief = await summarize(
        "Summarize current scholarship and internship opportunities for international "
        "students. For each: who's eligible and where to apply. End with a reminder to "
        "verify on the official university / DSU site, as deadlines change.",
        context,
    )
    return {
        "university": university, "field": field, "brief": brief,
        "sources": [{"title": w["title"], "url": w["url"]} for w in web],
        "disclaimer": "Deadlines change often - confirm on the official university/DSU site.",
    }

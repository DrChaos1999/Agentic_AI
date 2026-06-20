"""Tool 2 — news a foreign student should actually know."""
from app.services.feeds import fetch_student_feeds
from app.services.websearch import web_search
from app.llm import summarize


async def student_news(topic: str | None = None, region: str | None = None) -> dict:
    items = await fetch_student_feeds(limit_each=8)

    web = []
    if topic:
        web = await web_search(f"Italy international students {topic} {region or ''} news")

    lines = [f"- {i['title']}: {i['summary']} ({i['link']})" for i in items]
    lines += [f"- {w['title']}: {w['snippet']} ({w['url']})" for w in web]
    context = "\n".join(lines)

    brief = await summarize(
        "From these items, pick the 5 most relevant to an international student living "
        "in Italy. For each: one line plus why it matters. Especially flag strikes "
        "(sciopero), visa/permesso rule changes, university deadlines, and public-health "
        "notices. If a topic was requested, prioritize it.",
        context + (f"\n\nRequested topic: {topic}" if topic else ""),
    )
    return {
        "topic": topic,
        "brief": brief,
        "sources": [{"title": i["title"], "url": i["link"]} for i in items[:8]],
    }

"""Free web search via DuckDuckGo (no API key)."""
import asyncio
from app.config import settings

try:
    from ddgs import DDGS
except ImportError:  # older package name
    from duckduckgo_search import DDGS  # type: ignore


def _search(query: str, n: int) -> list[dict]:
    with DDGS() as d:
        return [
            {"title": r.get("title", ""), "snippet": r.get("body", ""),
             "url": r.get("href", "")}
            for r in d.text(query, max_results=n)
        ]


async def web_search(query: str, n: int = 5) -> list[dict]:
    if not settings.ENABLE_WEB_SEARCH:
        return []
    try:
        return await asyncio.to_thread(_search, query, n)
    except Exception:
        return []

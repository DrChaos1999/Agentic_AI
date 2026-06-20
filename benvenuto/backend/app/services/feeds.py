"""RSS fetching via feedparser (free). Used by news + scholarship tools."""
import asyncio
import feedparser

# A few student-relevant English feeds. Add university feeds as you find them.
STUDENT_FEEDS = [
    "https://www.ansa.it/english/english_rss.xml",
    "https://www.thelocal.it/feeds/rss.php",
]


def _parse(url: str, limit: int) -> list[dict]:
    f = feedparser.parse(url)
    return [{
        "title": getattr(e, "title", ""),
        "summary": getattr(e, "summary", "")[:400],
        "link": getattr(e, "link", ""),
        "published": getattr(e, "published", ""),
    } for e in f.entries[:limit]]


async def fetch_feed(url: str, limit: int = 8) -> list[dict]:
    try:
        return await asyncio.to_thread(_parse, url, limit)
    except Exception:
        return []


async def fetch_student_feeds(limit_each: int = 6) -> list[dict]:
    items: list[dict] = []
    for url in STUDENT_FEEDS:
        items += await fetch_feed(url, limit_each)
    return items

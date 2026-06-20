"""Tool 5 — what to say & how to behave to socialize, with Italian phrases.

Returns a `phrases` list ([{it, en}]) the backend can turn into audio with TTS.
"""
import json
from app.rag.store import rag_query
from app.llm import summarize
from app.config import settings


async def _extract_phrases(text: str) -> list[dict]:
    raw = await summarize(
        "From the text, extract 3-5 useful Italian phrases. Return ONLY a JSON array "
        "of objects like {\"it\": \"...\", \"en\": \"...\"}. No prose, no code fences.",
        text,
    )
    try:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        return data if isinstance(data, list) else []
    except Exception:
        return []


async def etiquette_coach(situation: str) -> dict:
    docs = await rag_query("etiquette", situation, k=4)
    context = "\n\n".join(docs) or f"General Italian social etiquette for: {situation}"

    brief = await summarize(
        "Advise what to say and how to behave in this Italian social situation. Cover "
        "formality (lei vs tu), greetings, and any gestures or do/don'ts. Then list a few "
        "useful Italian phrases with English meanings.",
        context + f"\n\nSituation: {situation}",
    )
    phrases = await _extract_phrases(brief)
    return {
        "situation": situation,
        "brief": brief,
        "phrases": phrases,
        "tts_hint": "POST any phrase['it'] to /speak to hear the pronunciation.",
    }

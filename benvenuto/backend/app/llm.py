"""Thin async wrappers around every OpenAI model used in Benvenuto."""
from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


# ---- Text / reasoning -------------------------------------------------------
async def summarize(instruction: str, context: str) -> str:
    """Cheap per-tool summarization with gpt-4o-mini."""
    resp = await client.chat.completions.create(
        model=settings.MODEL_SUMMARIZER,
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": context[:12000] or "(no source material found)"},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


# ---- Embeddings -------------------------------------------------------------
async def embed(text: str) -> list[float]:
    resp = await client.embeddings.create(model=settings.MODEL_EMBED, input=text[:8000])
    return resp.data[0].embedding


# ---- Safety -----------------------------------------------------------------
async def moderate(text: str) -> bool:
    """Return True if the text is flagged as unsafe."""
    try:
        r = await client.moderations.create(model=settings.MODEL_MODERATION, input=text)
        return r.results[0].flagged
    except Exception:
        return False  # fail open on moderation outages; log in production


# ---- Voice ------------------------------------------------------------------
async def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    resp = await client.audio.transcriptions.create(
        model=settings.MODEL_WHISPER, file=(filename, audio_bytes)
    )
    return resp.text


async def speak(text: str, voice: str = "alloy") -> bytes:
    resp = await client.audio.speech.create(
        model=settings.MODEL_TTS, voice=voice, input=text[:4000]
    )
    return resp.read()


# ---- Vision -----------------------------------------------------------------
async def describe_image(image_b64: str, prompt: str) -> str:
    resp = await client.chat.completions.create(
        model=settings.MODEL_VISION,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        ]}],
    )
    return resp.choices[0].message.content or ""

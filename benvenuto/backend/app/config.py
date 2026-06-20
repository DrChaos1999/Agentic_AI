"""Single source of truth for settings and model names. Reads from .env."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ---- OpenAI ----
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ---- Model map (override in .env, nowhere else) ----
    MODEL_ORCHESTRATOR: str = os.getenv("MODEL_ORCHESTRATOR", "gpt-4o")
    MODEL_SUMMARIZER: str = os.getenv("MODEL_SUMMARIZER", "gpt-4o-mini")
    MODEL_EMBED: str = os.getenv("MODEL_EMBED", "text-embedding-3-small")
    MODEL_WHISPER: str = os.getenv("MODEL_WHISPER", "whisper-1")
    MODEL_TTS: str = os.getenv("MODEL_TTS", "tts-1")
    MODEL_VISION: str = os.getenv("MODEL_VISION", "gpt-4o")
    MODEL_MODERATION: str = os.getenv("MODEL_MODERATION", "omni-moderation-latest")

    # ---- App ----
    CHROMA_DIR: str = os.getenv("CHROMA_DIR", "./chroma_db")
    OSM_USER_AGENT: str = os.getenv(
        "OSM_USER_AGENT", "benvenuto-student-guide/1.0 (set-your-email@example.com)"
    )
    ENABLE_WEB_SEARCH: bool = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"

    # CORS origins for the frontend dev server
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")


settings = Settings()

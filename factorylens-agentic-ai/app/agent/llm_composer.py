from __future__ import annotations

import json
from typing import Any

from app.core.config import Settings


class LLMComposer:
    """Optional LLM narrator. It may explain evidence but cannot change tool outputs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def compose(self, evidence: dict[str, Any], fallback: str) -> str:
        if not (self.settings.enable_llm and self.settings.openai_api_key):
            return fallback
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.settings.openai_api_key)
            prompt = (
                "You are a cautious industrial maintenance assistant. Summarize the supplied "
                "machine-vision evidence in 120 words or fewer. Do not invent facts, do not alter "
                "risk scores, and state that a qualified human must verify the recommendation.\n\n"
                + json.dumps(evidence, ensure_ascii=False)
            )
            response = client.responses.create(model=self.settings.openai_model, input=prompt)
            text = getattr(response, "output_text", "").strip()
            return text or fallback
        except Exception:
            return fallback

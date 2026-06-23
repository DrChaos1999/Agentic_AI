from app.config import get_settings
from app.schemas import OrderExtraction
from app.utils.text import normalize_text


class ParserUnavailableError(RuntimeError):
    pass


class OpenAIOrderParser:
    """Optional LLM parser using OpenAI structured outputs."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_enabled:
            raise ParserUnavailableError(
                "OpenAI parser requires OPENAI_API_KEY and OPENAI_MODEL in the environment."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ParserUnavailableError("Install the openai package to use OpenAI mode.") from exc

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def parse(self, message: str) -> OrderExtraction:
        system_prompt = """
You extract e-commerce orders from informal Bangla, Banglish, and English messages.
Return only the supplied schema. Normalize products and colors to concise English.
Use quantity as an integer. Interpret 'আগের address', 'same address', and similar wording
as 'previous address'. delivery_date should be a semantic label such as today, tomorrow,
day_after_tomorrow, or an explicit date. Required fields are product, quantity, and address.
List absent required fields in missing_fields. Never invent information.
""".strip()
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            text_format=OrderExtraction,
        )
        parsed = response.output_parsed
        parsed.normalized_message = normalize_text(message)
        parsed.parser_used = "openai"
        parsed.missing_fields = [
            field for field in ("product", "quantity", "address") if not getattr(parsed, field)
        ]
        return parsed

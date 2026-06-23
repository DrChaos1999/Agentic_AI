from app.config import get_settings
from app.parsers.openai_parser import OpenAIOrderParser, ParserUnavailableError
from app.parsers.rule_based import RuleBasedBanglaOrderParser
from app.schemas import OrderExtraction, ParserMode


def parse_order_message(message: str, mode: ParserMode = "auto") -> OrderExtraction:
    settings = get_settings()

    if mode == "rule":
        return RuleBasedBanglaOrderParser().parse(message)

    if mode == "openai":
        return OpenAIOrderParser().parse(message)

    if settings.openai_enabled:
        try:
            return OpenAIOrderParser().parse(message)
        except ParserUnavailableError:
            pass
        except Exception:
            # Auto mode remains usable when the external provider is temporarily unavailable.
            pass

    return RuleBasedBanglaOrderParser().parse(message)

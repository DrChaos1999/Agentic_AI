import hashlib
import re
import unicodedata


_BANGLA_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_ALLOWED_SYMBOLS = set("@+./:#-")


def convert_bangla_digits(text: str) -> str:
    return text.translate(_BANGLA_DIGITS)


def normalize_text(text: str) -> str:
    """Normalize case and spacing while preserving Bengali vowel signs/marks."""
    normalized = unicodedata.normalize("NFC", convert_bangla_digits(text)).lower()
    normalized = normalized.replace("–", "-").replace("—", "-")
    kept: list[str] = []
    for char in normalized:
        category = unicodedata.category(char)
        if category[0] in {"L", "N", "M"} or char.isspace() or char in _ALLOWED_SYMBOLS:
            kept.append(char)
        else:
            kept.append(" ")
    return re.sub(r"\s+", " ", "".join(kept)).strip()


def stable_message_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()

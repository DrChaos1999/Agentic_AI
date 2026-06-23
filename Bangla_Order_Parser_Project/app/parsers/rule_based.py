import re
from datetime import date, timedelta

from app.schemas import OrderExtraction
from app.utils.text import normalize_text


PRODUCT_ALIASES: dict[str, tuple[str, ...]] = {
    "t-shirt": ("t-shirt", "tshirt", "tee shirt", "টি-শার্ট", "টি শার্ট", "টিশার্ট"),
    "shirt": ("shirt", "shirts", "শার্ট"),
    "pants": ("pant", "pants", "trouser", "trousers", "প্যান্ট", "ট্রাউজার"),
    "panjabi": ("panjabi", "punjabi", "পাঞ্জাবি"),
    "saree": ("saree", "sari", "শাড়ি", "শাড়ি"),
    "shoes": ("shoe", "shoes", "sneaker", "sneakers", "জুতা"),
    "hoodie": ("hoodie", "হুডি"),
}

COLOR_ALIASES: dict[str, tuple[str, ...]] = {
    "blue": ("blue", "নীল"),
    "red": ("red", "লাল"),
    "black": ("black", "কালো"),
    "white": ("white", "সাদা"),
    "green": ("green", "সবুজ"),
    "yellow": ("yellow", "হলুদ"),
    "pink": ("pink", "গোলাপি"),
    "gray": ("gray", "grey", "ধূসর"),
    "brown": ("brown", "বাদামি"),
    "orange": ("orange", "কমলা"),
    "purple": ("purple", "বেগুনি"),
}

NUMBER_WORDS: dict[str, int] = {
    "এক": 1,
    "একটা": 1,
    "একটি": 1,
    "one": 1,
    "দুই": 2,
    "দুইটা": 2,
    "দুইটি": 2,
    "দুটা": 2,
    "two": 2,
    "তিন": 3,
    "তিনটা": 3,
    "তিনটি": 3,
    "three": 3,
    "চার": 4,
    "চারটা": 4,
    "চারটি": 4,
    "four": 4,
    "পাঁচ": 5,
    "পাঁচটা": 5,
    "five": 5,
    "ছয়": 6,
    "ছয়": 6,
    "six": 6,
    "সাত": 7,
    "seven": 7,
    "আট": 8,
    "eight": 8,
    "নয়": 9,
    "নয়": 9,
    "nine": 9,
    "দশ": 10,
    "ten": 10,
}


class RuleBasedBanglaOrderParser:
    """A transparent baseline parser for common Bangla and Banglish orders."""

    required_fields = ("product", "quantity", "address")

    def parse(self, message: str) -> OrderExtraction:
        text = normalize_text(message)
        product = self._find_alias(text, PRODUCT_ALIASES)
        quantity = self._extract_quantity(text)
        size = self._extract_size(text)
        color = self._find_alias(text, COLOR_ALIASES)
        delivery_label, delivery_iso = self._extract_delivery_date(text)
        address = self._extract_address(text)
        customer_name = self._extract_labeled_value(text, ("name", "customer", "নাম"))
        phone = self._extract_phone(text)

        values = {
            "product": product,
            "quantity": quantity,
            "address": address,
        }
        missing_fields = [field for field in self.required_fields if not values[field]]
        optional_found = sum(bool(item) for item in (size, color, delivery_label, customer_name, phone))
        required_found = len(self.required_fields) - len(missing_fields)
        confidence = min(0.98, 0.25 + required_found * 0.20 + optional_found * 0.05)

        return OrderExtraction(
            product=product,
            quantity=quantity,
            size=size,
            color=color,
            delivery_date=delivery_label,
            delivery_date_iso=delivery_iso,
            address=address,
            customer_name=customer_name,
            phone=phone,
            missing_fields=missing_fields,
            confidence=round(confidence, 2),
            normalized_message=text,
            parser_used="rule",
        )

    @staticmethod
    def _find_alias(text: str, aliases: dict[str, tuple[str, ...]]) -> str | None:
        for canonical, options in aliases.items():
            for alias in sorted(options, key=len, reverse=True):
                if alias in text:
                    return canonical
        return None

    @staticmethod
    def _extract_quantity(text: str) -> int | None:
        patterns = (
            r"(?<!\d)(\d{1,3})\s*(?:টা|টি|pcs?|pieces?|units?)(?!\w)",
            r"(?:qty|quantity|পরিমাণ)\s*[:=-]?\s*(\d{1,3})",
        )
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.UNICODE)
            if match:
                value = int(match.group(1))
                return value if value > 0 else None

        for word, value in sorted(NUMBER_WORDS.items(), key=lambda item: len(item[0]), reverse=True):
            if word in text:
                return value
        return None

    @staticmethod
    def _extract_size(text: str) -> str | None:
        match = re.search(r"(?<!\w)(xxxl|xxl|xl|l|m|s)(?!\w)", text, flags=re.IGNORECASE)
        return match.group(1).upper() if match else None

    @staticmethod
    def _extract_delivery_date(text: str) -> tuple[str | None, date | None]:
        today = date.today()
        if re.search(r"day after tomorrow|পরশু", text):
            return "day_after_tomorrow", today + timedelta(days=2)
        if re.search(r"tomorrow|কালকে|আগামীকাল|কাল", text):
            return "tomorrow", today + timedelta(days=1)
        if re.search(r"today|আজকে|আজ", text):
            return "today", today
        iso_match = re.search(r"(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)", text)
        if iso_match:
            try:
                parsed = date.fromisoformat(iso_match.group(1))
                return iso_match.group(1), parsed
            except ValueError:
                pass
        return None, None

    @staticmethod
    def _extract_address(text: str) -> str | None:
        if re.search(r"(আগের\s+(?:address|ঠিকানা)|previous\s+address|same\s+address)", text):
            return "previous address"

        match = re.search(
            r"(?:address|ঠিকানা)\s*[:=-]?\s*(.+?)(?=\s+(?:phone|mobile|ফোন|মোবাইল|name|নাম)\s*[:=-]?|$)",
            text,
            flags=re.UNICODE,
        )
        if not match:
            return None
        value = match.group(1).strip(" .,-")
        value = re.sub(r"\s+(?:এ|তে)?\s*(?:পাঠাবেন|পাঠান|send|deliver).*$", "", value).strip()
        return value or None

    @staticmethod
    def _extract_phone(text: str) -> str | None:
        match = re.search(r"(?<!\d)(?:\+?88)?01[3-9]\d{8}(?!\d)", text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_labeled_value(text: str, labels: tuple[str, ...]) -> str | None:
        label_pattern = "|".join(re.escape(label) for label in labels)
        match = re.search(
            rf"(?:{label_pattern})\s*[:=-]\s*([\w .'-]+?)(?=\s+(?:phone|mobile|ফোন|মোবাইল|address|ঠিকানা)\s*[:=-]?|$)",
            text,
            flags=re.UNICODE,
        )
        return match.group(1).strip() if match else None

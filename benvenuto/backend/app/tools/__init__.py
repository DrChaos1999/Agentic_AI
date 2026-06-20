"""Registry mapping each tool name to its callable and its OpenAI schema."""
from app.tools.law import law_info
from app.tools.news import student_news
from app.tools.cuisine import cuisine_guide
from app.tools.tourism import tourism_guide
from app.tools.etiquette import etiquette_coach
from app.tools.grocery import grocery_finder
from app.tools.university_area import university_area
from app.tools.scholarships import scholarships

TOOL_REGISTRY = {
    "law_info": law_info,
    "student_news": student_news,
    "cuisine_guide": cuisine_guide,
    "tourism_guide": tourism_guide,
    "etiquette_coach": etiquette_coach,
    "grocery_finder": grocery_finder,
    "university_area": university_area,
    "scholarships": scholarships,
}


def _fn(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


TOOL_SCHEMAS = [
    _fn(
        "law_info",
        "Italian laws, rules, and official procedures for a specific activity or "
        "situation (immigration, residence permits, student work hours, renting, "
        "driving/ZTL, etc.).",
        {
            "topic": {"type": "string",
                      "description": "The legal topic or situation, e.g. 'travel within "
                                     "EU while permesso di soggiorno is pending'."},
            "region": {"type": "string",
                       "description": "Optional Italian region/city for local rules."},
        },
        ["topic"],
    ),
    _fn(
        "student_news",
        "Recent news an international student in Italy should know: visa/permesso rule "
        "changes, strikes (sciopero), university deadlines, public-health notices.",
        {
            "topic": {"type": "string", "description": "Optional topic to prioritize."},
            "region": {"type": "string", "description": "Optional region/city."},
        },
        [],
    ),
    _fn(
        "cuisine_guide",
        "Regional Italian dishes, food etiquette, what to eat or avoid, and ordering tips.",
        {
            "query": {"type": "string", "description": "The food question, e.g. "
                                                       "'typical breakfast'."},
            "region": {"type": "string", "description": "Optional region/city."},
        },
        ["query"],
    ),
    _fn(
        "tourism_guide",
        "Top tourist spots in an Italian region PLUS the specific scams and traps to avoid.",
        {
            "region": {"type": "string", "description": "Region or city, e.g. 'Venice'."},
            "interests": {"type": "string", "description": "Optional interests, e.g. "
                                                           "'art, food, nightlife'."},
        },
        ["region"],
    ),
    _fn(
        "etiquette_coach",
        "What to say and how to behave to socialize in a given Italian situation, with "
        "useful Italian phrases (which can be spoken aloud via TTS).",
        {
            "situation": {"type": "string", "description": "The social situation, e.g. "
                                                           "'meeting my professor for the "
                                                           "first time'."},
        },
        ["situation"],
    ),
    _fn(
        "grocery_finder",
        "Where to buy a specific item or ingredient near a location in Italy.",
        {
            "item": {"type": "string", "description": "The item to buy, e.g. "
                                                      "'basmati rice'."},
            "location": {"type": "string", "description": "Area/city, e.g. "
                                                          "'near Politecnico di Milano'."},
        },
        ["item", "location"],
    ),
    _fn(
        "university_area",
        "Practical info about the area around a specific Italian university: transport, "
        "supermarkets, pharmacies, banks, cafes.",
        {
            "university": {"type": "string", "description": "University name, e.g. "
                                                            "'Sapienza University Rome'."},
            "categories": {"type": "array", "items": {"type": "string"},
                           "description": "Optional amenity types, e.g. "
                                          "['pharmacy','supermarket','subway_entrance']."},
        },
        ["university"],
    ),
    _fn(
        "scholarships",
        "Scholarship and internship opportunities for international students at a "
        "specific Italian university.",
        {
            "university": {"type": "string", "description": "University name."},
            "field": {"type": "string", "description": "Optional field of study."},
        },
        ["university"],
    ),
]

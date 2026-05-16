from __future__ import annotations

import json
import re
import unicodedata
from datetime import UTC, datetime

SKILL_STOPWORDS = {
    "con", "del", "las", "los", "para", "por", "que", "una", "unos", "unas",
    "and", "the", "when", "use", "using", "user", "from", "this", "that",
    "como", "cuando", "donde", "este", "esta", "estos", "estas", "algo",
    "antes", "despues", "sobre", "tiene", "tener", "hacer", "hace", "hacia",
    "hacia", "hacía", "quiero", "necesito", "cual", "cuál", "era", "sirve",
    "ayuda", "ayudar", "alguna", "alguno", "tenemos", "skill", "skills",
    "proyecto", "proyectos", "crear", "crea",
}

def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def normalize_json_array(values: list[str] | tuple[str, ...] | None) -> list[str]:
    if not values:
        return []
    normalized = []
    for value in values:
        item = str(value).strip()
        if item and item not in normalized:
            normalized.append(item)
    return normalized


def parse_json_array(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()]


def skill_reference_tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return {
        token for token in re.findall(r"[a-z0-9][a-z0-9_/-]{2,}", normalized)
        if token not in SKILL_STOPWORDS
    }

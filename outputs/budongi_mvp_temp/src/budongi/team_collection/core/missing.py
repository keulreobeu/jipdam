from __future__ import annotations

import re

SEMANTIC_TOKENS: frozenset[str] = frozenset({"", "-", "미상", "0000", "99991231"})
"""Frozenset of exact string tokens indicating missing values."""

_PHONE_SEPARATORS = str.maketrans("", "", "- ().")
_PLACEHOLDER_PATTERN = r"(?:02|0[3-6][1-5]|01[016789]|070)0+"


def is_placeholder_phone(text: str) -> bool:
    """Return True when text is a placeholder phone number, else False."""
    if not isinstance(text, str):
        return False
    d = text.translate(_PHONE_SEPARATORS)
    if len(d) < 7:
        return False
    if not all("0" <= c <= "9" for c in d):
        return False
    if all(c == "0" for c in d):
        return True
    return re.fullmatch(_PLACEHOLDER_PATTERN, d) is not None


def classify_value(
    value: object,
    *,
    kind: str = "text",
    extra: frozenset[str] = frozenset(),
) -> str:
    """Classify a raw cell value as null, semantic-missing, or present."""
    if value is None:
        return "null"
    if not isinstance(value, str):
        return "present"
    s = value.strip()
    if s in SEMANTIC_TOKENS:
        return "semantic"
    if s in extra:
        return "semantic"
    if kind == "phone" and is_placeholder_phone(s):
        return "semantic"
    return "present"

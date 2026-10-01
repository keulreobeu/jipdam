"""Small compatibility helpers adapted from the prior repository's preprocessing.

Source: 01_preprocessing/preprocess_apartment_pipeline.py at
https://github.com/keulreobeu/Real_estate_Chatbot_by_gemma4
The old flat CSV describes supply/listing facts, not verified transactions.
"""

from __future__ import annotations

import csv
from pathlib import Path


def read_legacy_csv(path: Path) -> tuple[list[dict[str, str]], str]:
    # Preserve the old pipeline's Korean CSV encoding fallback without pandas.
    for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            with path.open("r", encoding=encoding, newline="") as stream:
                return list(csv.DictReader(stream)), encoding
        except UnicodeError:
            continue
    raise ValueError(f"CSV encoding could not be detected: {path}")


def parse_address(address: str | None) -> dict[str, str | None]:
    """Split Korean legal address into province, district and neighborhood."""
    result: dict[str, str | None] = {"province": None, "district": None, "neighborhood": None}
    if not address or not address.strip():
        return result
    tokens = " ".join(address.split()).split(" ")
    result["province"] = tokens[0]
    if len(tokens) >= 4 and tokens[1].endswith("시") and tokens[2].endswith(("구", "군")):
        result["district"] = f"{tokens[1]} {tokens[2]}"
        result["neighborhood"] = tokens[3]
    elif len(tokens) >= 3:
        result["district"] = tokens[1]
        result["neighborhood"] = tokens[2]
    elif len(tokens) >= 2:
        result["district"] = tokens[1]
    return result

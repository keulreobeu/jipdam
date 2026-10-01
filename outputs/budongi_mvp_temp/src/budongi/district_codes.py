"""Map provisional addresses to official legal district codes for API queries."""

from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from collections import defaultdict
from pathlib import Path


PROVINCE_ALIASES = {"서울시": "서울특별시", "인천시": "인천광역시"}
ADDRESS_ALIASES = {
    "경기도 고양덕양구": "경기도 고양시 덕양구",
    "경기도 성남수정구": "경기도 성남시 수정구",
    "경기도 용인처인구": "경기도 용인시 처인구",
}

# The trade API currently serves older contract months under newer district codes.
# These are query scopes, never automatic proof that an old apartment belongs to
# a particular successor district.
SUCCESSOR_QUERY_CODES = {
    "28110": ("28125", "28155"),  # old Incheon Jung-gu
    "28140": ("28125",),           # old Incheon Dong-gu
    "28260": ("28275", "28290"),  # old Incheon Seo-gu
    "41110": ("41111", "41113", "41115", "41117"),  # Suwon city-level addresses
    "41190": ("41192", "41194", "41196"),  # Bucheon
    "41590": ("41591", "41593", "41595", "41597"),  # Hwaseong
}


def query_codes_for_catalog_code(code: str) -> tuple[str, ...]:
    return SUCCESSOR_QUERY_CODES.get(code, (code,))


def official_districts(archive: Path) -> tuple[dict[str, str], str]:
    raw = archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        if len(bundle.namelist()) != 1:
            raise ValueError("Expected one code list in the official archive")
        rows = csv.reader(io.StringIO(bundle.read(bundle.namelist()[0]).decode("cp949")), delimiter="\t")
        if next(rows) != ["법정동코드", "법정동명", "폐지여부"]:
            raise ValueError("Unexpected legal district code list header")
        names: dict[str, set[tuple[str, str]]] = defaultdict(set)
        for code, name, status in rows:
            if len(code) == 10 and code.endswith("00000") and not code.endswith("00000000"):
                names[name].add((code[:5], status))
    resolved = {}
    for name, candidates in names.items():
        current = [code for code, status in candidates if status == "존재"]
        if len(current) == 1:
            resolved[name] = current[0]
        elif len(candidates) == 1:
            resolved[name] = next(iter(candidates))[0]
    return resolved, hashlib.sha256(raw).hexdigest()


def district_for_address(address: str, districts: dict[str, str]) -> tuple[str | None, str | None]:
    parts = address.strip().split()
    if not parts:
        return None, None
    parts[0] = PROVINCE_ALIASES.get(parts[0], parts[0])
    normalized = " ".join(parts)
    for before, after in ADDRESS_ALIASES.items():
        if normalized.startswith(before + " "):
            normalized = after + normalized[len(before):]
            break
    matches = [name for name in districts if normalized == name or normalized.startswith(name + " ")]
    if not matches:
        return None, None
    longest = max(matches, key=len)
    return districts[longest], longest

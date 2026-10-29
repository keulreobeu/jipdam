"""Gate 12: no API key, in any encoding, may appear in a package tree or ZIP (ROLE2-COLLECT-001-REQ-03)."""
from __future__ import annotations

import html
import re
import urllib.parse
import zipfile
from pathlib import Path

PATTERNS = (
    re.compile(r"(?i)service_?key=[^&\s\"'<]{8,}"),
    re.compile(r"(?i)openapi\.seoul\.go\.kr:8088/(?!sample/|\{KEY\}/)[^/\s\"'<]{20,}/"),
)


def key_forms(key: str) -> set:
    forms = {key, urllib.parse.quote(key, safe=""), urllib.parse.quote_plus(key), urllib.parse.unquote(key),
             html.escape(key)}
    return {f for f in forms if len(f) >= 8}


def _hits(data: bytes, forms: set) -> bool:
    text = data.decode("utf-8", errors="replace").casefold()
    return any(form.casefold() in text or form.encode("utf-8") in data for form in forms)


def pattern_hits(data: bytes) -> list:
    text = data.decode("utf-8", errors="replace")
    return [p.pattern for p in PATTERNS if p.search(text)]


def sweep_tree(root: Path, keys: list) -> list:
    """Relative paths (posix) whose bytes contain a key form or a key-shaped URL."""
    forms = set().union(*(key_forms(k) for k in keys)) if keys else set()
    found = []
    for path in sorted(p for p in Path(root).rglob("*") if p.is_file()):
        data = path.read_bytes()
        if (forms and _hits(data, forms)) or pattern_hits(data):
            found.append(path.relative_to(root).as_posix())
    return found


def sweep_zip(archive: Path, keys: list) -> list:
    forms = set().union(*(key_forms(k) for k in keys)) if keys else set()
    found = []
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            data = zf.read(info)
            name_hit = forms and _hits(info.filename.encode("utf-8"), forms)
            if name_hit or (forms and _hits(data, forms)) or pattern_hits(data):
                found.append(info.filename)
    return found

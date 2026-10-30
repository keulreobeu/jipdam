from __future__ import annotations

import json

from budongi.team_collection import contract as C
from budongi.team_collection.base import ParsedPage


def parse_page(payload: bytes, *, service: str) -> tuple[ParsedPage, str]:
    """Decode and parse one Seoul open-data JSON response for the named service."""
    if not isinstance(payload, bytes) or isinstance(payload, bytearray):
        raise C.ContractError("invalid_payload")
    if not isinstance(service, str) or not service:
        raise C.ContractError("invalid_service")

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        raise C.ContractError("decode_error")

    try:
        doc = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        raise C.ContractError("invalid_payload")

    if not isinstance(doc, dict):
        raise C.ContractError("invalid_payload")

    if service in doc:
        inner = doc[service]
        if not isinstance(inner, dict):
            raise C.ContractError("invalid_payload")

        if "RESULT" not in inner or not isinstance(inner["RESULT"], dict):
            raise C.ContractError("invalid_payload")

        result = inner["RESULT"]
        if "CODE" not in result or not isinstance(result["CODE"], str):
            raise C.ContractError("invalid_payload")

        code = result["CODE"]

        raw_rows = inner.get("row")
        if raw_rows is None:
            rows: tuple[dict, ...] = ()
        elif isinstance(raw_rows, list):
            for item in raw_rows:
                if not isinstance(item, dict):
                    raise C.ContractError("invalid_payload")
            rows = tuple(raw_rows)
        else:
            raise C.ContractError("invalid_payload")

        if "list_total_count" not in inner:
            total: int | None = None
        else:
            raw_total = inner["list_total_count"]
            if isinstance(raw_total, bool) or not isinstance(raw_total, int) or raw_total < 0:
                raise C.ContractError("invalid_payload")
            total = raw_total

        status = "ok" if len(rows) > 0 else "empty"
        return ParsedPage(rows=rows, total=total, status=status), code

    if "RESULT" in doc and isinstance(doc["RESULT"], dict):
        result = doc["RESULT"]
        if "CODE" not in result or not isinstance(result["CODE"], str):
            raise C.ContractError("invalid_payload")
        code = result["CODE"]
        return ParsedPage(rows=(), total=None, status="empty"), code

    raise C.ContractError("invalid_payload")


def window_params(total: int, *, size: int = 1000) -> tuple[tuple[int, int], ...]:
    """Return consecutive 1-based inclusive (start, end) windows covering total rows."""
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise C.ContractError("invalid_total")
    if isinstance(size, bool) or not isinstance(size, int) or not (1 <= size <= 1000):
        raise C.ContractError("invalid_size")

    if total == 0:
        return ()

    windows: list[tuple[int, int]] = []
    start = 1
    while start <= total:
        end = min(start + size - 1, total)
        windows.append((start, end))
        start += size

    return tuple(windows)

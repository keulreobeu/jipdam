"""Reconcile team_collection_v1 row counts and build the validation.json document."""
from __future__ import annotations

import copy

from budongi.team_collection import contract as C

REJECTED_LIMIT = 200
"""Maximum number of rejected items copied into the document."""

_SECTION_COUNTS = ("raw", "accepted", "excluded", "rejected")
_DUPLICATE_KEYS = ("full_row", "source_position", "similar_entity")


def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _fail(code: str) -> C.ContractError:
    return C.ContractError(code)


def _validate(stats: object) -> tuple[list[dict], list[dict]]:
    """Validate the common stats keys; return (sections, requests)."""
    if not isinstance(stats, dict):
        raise _fail("invalid_stats:lane")
    lane = stats.get("lane")
    if not isinstance(lane, str) or lane not in C.LANES:
        raise _fail("invalid_stats:lane")
    sections = stats.get("sections")
    if not isinstance(sections, list):
        raise _fail("invalid_stats:sections")
    for entry in sections:
        if not isinstance(entry, dict) or not isinstance(entry.get("section"), str):
            raise _fail("invalid_stats:sections")
    names = [entry["section"] for entry in sections]
    if len(set(names)) != len(names):
        raise _fail("invalid_stats:duplicate_section")
    for entry in sections:
        for key in _SECTION_COUNTS:
            if not _is_count(entry.get(key)):
                raise _fail("invalid_stats:counts")
    if not _is_count(stats.get("jsonl_lines")):
        raise _fail("invalid_stats:jsonl_lines")
    requests = stats["requests"] if "requests" in stats else []
    if not isinstance(requests, list):
        raise _fail("invalid_stats:requests")
    for entry in requests:
        if not isinstance(entry, dict) or not isinstance(entry.get("request_id"), str):
            raise _fail("invalid_stats:requests")
    for entry in requests:
        if not _is_count(entry.get("received_rows")):
            raise _fail("invalid_stats:counts")
        expected = entry.get("expected_rows")
        if expected is not None and not _is_count(expected):
            raise _fail("invalid_stats:counts")
    return sections, requests


def reconcile(stats: dict) -> list[str]:
    """Return ordered reconciliation error codes for stats (empty when all counts reconcile)."""
    sections, requests = _validate(stats)
    errors: list[str] = []
    for entry in sections:
        if entry["raw"] != entry["accepted"] + entry["excluded"] + entry["rejected"]:
            errors.append("raw_mismatch:" + entry["section"])
    total_raw = sum(entry["raw"] for entry in sections)
    total_accepted = sum(entry["accepted"] for entry in sections)
    total_rejected = sum(entry["rejected"] for entry in sections)
    if stats["jsonl_lines"] != total_accepted + total_rejected:
        errors.append("jsonl_mismatch")
    if stats["lane"] not in C.FILE_LANES:
        if sum(entry["received_rows"] for entry in requests) != total_raw:
            errors.append("received_mismatch")
    for entry in requests:
        expected = entry.get("expected_rows")
        if (expected is not None and expected == entry["received_rows"]
                and entry.get("expected_basis") != "provider"):
            errors.append("expected_backfilled:" + entry["request_id"])
    return errors


def _optional(stats: dict, key: str, kind: type) -> object:
    value = stats.get(key)
    return value if isinstance(value, kind) else kind()


def _reject_item(row: object) -> dict:
    source = row if isinstance(row, dict) else {}
    return {key: copy.deepcopy(source.get(key)) for key in ("section", "position", "reason")}


def build_validation(stats: dict) -> dict:
    """Return the JSON-serializable validation.json document for stats."""
    sections, requests = _validate(stats)
    source_id = stats.get("source_id")
    if not isinstance(source_id, str) or not C.SOURCE_ID_RE.fullmatch(source_id):
        raise _fail("invalid_stats:source_id")
    batch_id = stats.get("batch_id")
    if not isinstance(batch_id, str) or not C.BATCH_ID_RE.fullmatch(batch_id):
        raise _fail("invalid_stats:batch_id")
    mapping_version = stats.get("mapping_version")
    if not isinstance(mapping_version, str) or not mapping_version:
        raise _fail("invalid_stats:mapping_version")
    validated_at = stats.get("validated_at_utc")
    if not isinstance(validated_at, str) or not C.UTC_Z_RE.fullmatch(validated_at):
        raise _fail("invalid_stats:validated_at_utc")

    errors = reconcile(stats)

    section_docs = []
    for entry in sections:
        section_docs.append({
            "section": entry["section"],
            "raw": entry["raw"],
            "accepted": entry["accepted"],
            "excluded": entry["excluded"],
            "rejected": entry["rejected"],
            "equal": entry["raw"] == entry["accepted"] + entry["excluded"] + entry["rejected"],
        })

    reconciliation = {
        "raw": sum(entry["raw"] for entry in sections),
        "accepted": sum(entry["accepted"] for entry in sections),
        "excluded": sum(entry["excluded"] for entry in sections),
        "rejected": sum(entry["rejected"] for entry in sections),
        "jsonl_lines": stats["jsonl_lines"],
        "received_rows": sum(entry["received_rows"] for entry in requests),
        "rows_equal_accepted_plus_excluded_plus_rejected": all(
            doc["equal"] for doc in section_docs),
        "ok": errors == [],
    }

    rejected_rows = _optional(stats, "rejected_rows", list)
    rejected = {
        "total": len(rejected_rows),
        "truncated": len(rejected_rows) > REJECTED_LIMIT,
        "items": [_reject_item(row) for row in rejected_rows[:REJECTED_LIMIT]],
    }

    counts: dict[str, int] = {}
    for reason in _optional(stats, "excluded_reasons", list):
        if isinstance(reason, str):
            counts[reason] = counts.get(reason, 0) + 1
    excluded_by_reason = {key: counts[key] for key in sorted(counts)}

    missing = _optional(stats, "missing_by_source_field", dict)
    missing_by_source_field = {
        key: copy.deepcopy(missing[key]) for key in sorted(missing, key=str)}

    duplicates_in = _optional(stats, "duplicates", dict)
    duplicates = {}
    for key in _DUPLICATE_KEYS:
        value = duplicates_in.get(key, 0)
        duplicates[key] = value if isinstance(value, int) and not isinstance(value, bool) else 0

    unmapped = sorted({item for item in _optional(stats, "unmapped_fields", list)
                       if isinstance(item, str)})

    parser = stats.get("parser")
    return {
        "delivery_schema_version": C.DELIVERY_SCHEMA_VERSION,
        "source_id": source_id,
        "batch_id": batch_id,
        "mapping_version": mapping_version,
        "validated_at_utc": validated_at,
        "lane": stats["lane"],
        "parser": copy.deepcopy(parser) if parser is not None else {},
        "reconciliation": reconciliation,
        "sections": section_docs,
        "rejected": rejected,
        "excluded_by_reason": excluded_by_reason,
        "missing_by_source_field": missing_by_source_field,
        "duplicates": duplicates,
        "coordinates": copy.deepcopy(_optional(stats, "coordinates", dict)),
        "unmapped_fields": unmapped,
        "pending_relations": copy.deepcopy(_optional(stats, "pending_relations", list)),
        "rerun": copy.deepcopy(stats.get("rerun")),
        "errors": errors,
    }

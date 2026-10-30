"""Transit route and stop-link record normalizers."""
from __future__ import annotations

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome
from budongi.team_collection.core.envelope import finalize


def _is_present(value: object) -> bool:
    """Return True if value is present according to rule R3."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    return True


def _parse_stop_sequence(val: object) -> tuple[bool, int | None]:
    """Parse stop_sequence according to rule R10."""
    if isinstance(val, int) and not isinstance(val, bool):
        if val >= 0:
            return True, val
        return False, None
    if isinstance(val, str):
        stripped = val.strip()
        if stripped and all("0" <= ch <= "9" for ch in stripped):
            return True, int(stripped)
        return False, None
    return False, None


def normalize_route(fields: dict, *, envelope: dict, namespace: str) -> Outcome:
    """Normalize a transit route record."""
    if not isinstance(namespace, str) or namespace.strip() == "":
        raise C.ContractError("invalid_namespace")

    record = dict(envelope)
    record.update(fields)
    record["entity_level"] = "network"
    record["identifier_namespace"] = namespace
    record["source_entity_id"] = fields.get("route_id")
    record["name"] = fields.get("route_name")

    if not _is_present(record["source_entity_id"]):
        status = "rejected"
        reason = "missing_required:source_entity_id"
    elif not _is_present(record["name"]):
        status = "rejected"
        reason = "missing_required:name"
    else:
        status = "accepted"
        reason = None

    finalized = finalize(record, status, reason)
    return Outcome(record=finalized, status=finalized["validation_status"], reason=finalized["validation_reason"])


def normalize_stop_link(
    fields: dict,
    *,
    envelope: dict,
    route_namespace: str,
    stop_namespace: str,
) -> Outcome:
    """Normalize a transit stop link record."""
    if not isinstance(route_namespace, str) or route_namespace.strip() == "":
        raise C.ContractError("invalid_namespace")
    if not isinstance(stop_namespace, str) or stop_namespace.strip() == "":
        raise C.ContractError("invalid_namespace")

    record = dict(envelope)
    record.update(fields)
    record["entity_level"] = "network"
    record["route_namespace"] = route_namespace
    record["source_route_id"] = fields.get("route_id")
    record["stop_namespace"] = stop_namespace
    record["source_stop_id"] = fields.get("stop_id")

    raw_seq = fields.get("stop_sequence")
    seq_present = _is_present(raw_seq)
    if seq_present:
        seq_valid, parsed_seq = _parse_stop_sequence(raw_seq)
        if seq_valid:
            record["stop_sequence"] = parsed_seq
        else:
            record["stop_sequence"] = None
            record["stop_sequence_raw"] = raw_seq
    else:
        record["stop_sequence"] = None
        seq_valid = False

    if not _is_present(record["source_route_id"]):
        status = "rejected"
        reason = "missing_required:source_route_id"
    elif not _is_present(record["source_stop_id"]):
        status = "rejected"
        reason = "missing_required:source_stop_id"
    elif not seq_present:
        status = "rejected"
        reason = "missing_required:stop_sequence"
    elif not seq_valid:
        status = "rejected"
        reason = "invalid_sequence"
    else:
        status = "accepted"
        reason = None

    finalized = finalize(record, status, reason)
    return Outcome(record=finalized, status=finalized["validation_status"], reason=finalized["validation_reason"])

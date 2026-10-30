"""Facility record normalizer."""
from __future__ import annotations

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome
from budongi.team_collection.core.envelope import finalize


def _is_present(value: object) -> bool:
    """Return True unless value is None or a whitespace-only string."""
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def normalize_facility(fields: dict, *, envelope: dict, type_namespace: str) -> Outcome:
    """Normalize a facility record from fields and envelope."""
    if not isinstance(type_namespace, str) or not type_namespace.strip():
        raise C.ContractError("invalid_namespace")

    record = dict(envelope)
    record.update(fields)
    record["entity_level"] = "facility"

    raw = fields.get("facility_type_raw")
    if _is_present(raw):
        record["facility_type_code"] = f"{type_namespace}:{raw}"
    else:
        record["facility_type_code"] = fields.get("facility_type_code")

    if not _is_present(record.get("name")):
        status = "rejected"
        reason = "missing_required:name"
    elif not _is_present(record.get("facility_type_code")):
        status = "rejected"
        reason = "missing_required:facility_type_code"
    else:
        status = "accepted"
        reason = None

    final_record = finalize(record, status, reason)
    return Outcome(
        record=final_record,
        status=final_record["validation_status"],
        reason=final_record["validation_reason"],
    )

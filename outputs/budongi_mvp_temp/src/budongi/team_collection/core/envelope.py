"""Record envelope builder, verdict finalizer, and validator."""
from __future__ import annotations

from dataclasses import dataclass

from budongi.team_collection import contract as C


@dataclass(frozen=True)
class BatchContext:
    """Frozen dataclass holding batch-level provenance."""

    source_id: str
    batch_id: str
    mapping_version: str
    record_type: str
    staged_at_utc: str
    source_retrieved_at_utc: str | None = None
    provided_at_utc: str | None = None
    source_date: str | None = None


def make_envelope(
    ctx: BatchContext,
    *,
    file_ref: str,
    file_sha: str,
    section: str,
    position: int | None = None,
    feature_id: str | None = None,
    column: int | None = None,
) -> dict:
    """Build a new provenance envelope dictionary for a source record."""
    try:
        source_id = ctx.source_id
    except AttributeError:
        source_id = None
    if not isinstance(source_id, str) or not C.SOURCE_ID_RE.match(source_id):
        raise C.ContractError("invalid_source_id")

    try:
        batch_id = ctx.batch_id
    except AttributeError:
        batch_id = None
    if not isinstance(batch_id, str) or len(batch_id) > C.BATCH_ID_MAX or not C.BATCH_ID_RE.match(batch_id):
        raise C.ContractError("invalid_batch_id")

    try:
        mapping_version = ctx.mapping_version
    except AttributeError:
        mapping_version = None
    if not isinstance(mapping_version, str) or not mapping_version.strip():
        raise C.ContractError("invalid_mapping_version")

    try:
        record_type = ctx.record_type
    except AttributeError:
        record_type = None
    if not isinstance(record_type, str) or record_type not in C.RECORD_TYPES:
        raise C.ContractError("invalid_record_type")

    try:
        staged_at_utc = ctx.staged_at_utc
    except AttributeError:
        staged_at_utc = None
    if not isinstance(staged_at_utc, str) or not C.UTC_Z_RE.match(staged_at_utc):
        raise C.ContractError("invalid_utc:staged_at_utc")

    try:
        source_retrieved_at_utc = ctx.source_retrieved_at_utc
    except AttributeError:
        source_retrieved_at_utc = None
    if source_retrieved_at_utc is not None:
        if not isinstance(source_retrieved_at_utc, str) or not C.UTC_Z_RE.match(source_retrieved_at_utc):
            raise C.ContractError("invalid_utc:source_retrieved_at_utc")

    try:
        provided_at_utc = ctx.provided_at_utc
    except AttributeError:
        provided_at_utc = None
    if provided_at_utc is not None:
        if not isinstance(provided_at_utc, str) or not C.UTC_Z_RE.match(provided_at_utc):
            raise C.ContractError("invalid_utc:provided_at_utc")

    try:
        source_date = ctx.source_date
    except AttributeError:
        source_date = None

    if not isinstance(file_ref, str) or not file_ref.strip():
        raise C.ContractError("invalid_file_ref")

    if not isinstance(file_sha, str) or not C.SHA256_RE.match(file_sha):
        raise C.ContractError("invalid_sha256")

    if not isinstance(section, str):
        raise C.ContractError("invalid_section")

    if (position is None and feature_id is None) or (position is not None and feature_id is not None):
        raise C.ContractError("invalid_position")
    if position is not None:
        if isinstance(position, bool) or not isinstance(position, int) or position < 1:
            raise C.ContractError("invalid_position")
    if feature_id is not None:
        if not isinstance(feature_id, str) or not feature_id.strip():
            raise C.ContractError("invalid_position")

    if column is not None:
        if isinstance(column, bool) or not isinstance(column, int) or column < 1:
            raise C.ContractError("invalid_column")

    env: dict[str, object] = {k: None for k in C.ENVELOPE_FIELDS + C.LOCATION_FIELDS}
    env["delivery_schema_version"] = C.DELIVERY_SCHEMA_VERSION
    env["quality_status"] = C.QUALITY_STATUS
    env["source_id"] = source_id
    env["batch_id"] = batch_id
    env["mapping_version"] = mapping_version
    env["record_type"] = record_type
    env["staged_at_utc"] = staged_at_utc
    env["source_retrieved_at_utc"] = source_retrieved_at_utc
    env["provided_at_utc"] = provided_at_utc
    env["source_date"] = source_date
    env["source_file_ref"] = file_ref
    env["source_content_sha256"] = file_sha
    env["source_section"] = section
    env["source_row_number"] = position
    env["source_feature_id"] = feature_id
    env["source_column_number"] = column
    return env


def finalize(record: dict, status: str, reason: str | None = None) -> dict:
    """Return a shallow copy of record with validation verdict fields set."""
    if not isinstance(record, dict):
        raise C.ContractError("invalid_record")
    if not isinstance(status, str) or status not in C.VALIDATION_STATUSES:
        raise C.ContractError("invalid_status")
    if status == "accepted":
        if reason is not None:
            raise C.ContractError("reason_forbidden")
    else:
        if reason is None or (isinstance(reason, str) and not reason.strip()):
            raise C.ContractError("reason_required")
        if not isinstance(reason, str):
            raise C.ContractError("unknown_reason")
        base = reason.split(":", 1)[0]
        if base not in C.REASONS:
            raise C.ContractError("unknown_reason")
        if C.REASONS[base] != status:
            raise C.ContractError("reason_status_mismatch")

    out = dict(record)
    out["validation_status"] = status
    out["validation_reason"] = reason
    return out


def validate_envelope(record: dict) -> list[str]:
    """Return a list of envelope error codes for record, empty when valid."""
    if not isinstance(record, dict):
        return ["not_a_dict"]

    codes: list[str] = []

    for key in C.ENVELOPE_FIELDS + C.LOCATION_FIELDS:
        if key not in record:
            codes.append(f"missing_key:{key}")

    if "delivery_schema_version" in record and record["delivery_schema_version"] != C.DELIVERY_SCHEMA_VERSION:
        codes.append("invalid_schema_version")

    if "quality_status" in record and record["quality_status"] != C.QUALITY_STATUS:
        codes.append("invalid_quality_status")

    if "record_type" in record:
        rt = record["record_type"]
        if not isinstance(rt, str) or rt not in C.RECORD_TYPES:
            codes.append("invalid_record_type")

    if "source_content_sha256" in record:
        sha = record["source_content_sha256"]
        if not isinstance(sha, str) or not C.SHA256_RE.match(sha):
            codes.append("invalid_sha256")

    if "source_row_number" in record and "source_feature_id" in record:
        row_none = record["source_row_number"] is None
        feat_none = record["source_feature_id"] is None
        if row_none == feat_none:
            codes.append("invalid_position")

    utc_keys = sorted(k for k in record if isinstance(k, str) and k.endswith("_utc"))
    for k in utc_keys:
        val = record[k]
        if k == "staged_at_utc":
            if val is None or not isinstance(val, str) or not C.UTC_Z_RE.match(val):
                codes.append(f"invalid_utc:{k}")
        else:
            if val is not None and (not isinstance(val, str) or not C.UTC_Z_RE.match(val)):
                codes.append(f"invalid_utc:{k}")

    if "latitude" in record and "longitude" in record:
        lat_none = record["latitude"] is None
        lon_none = record["longitude"] is None
        if lat_none != lon_none:
            codes.append("partial_coordinates")

    if "validation_status" in record:
        status = record["validation_status"]
        if status is None:
            codes.append("not_finalized")
        else:
            reason = record.get("validation_reason", None)
            if not isinstance(status, str) or status not in C.VALIDATION_STATUSES:
                codes.append("invalid_status")
            elif status == "accepted":
                if reason is not None:
                    codes.append("reason_forbidden")
            else:
                if reason is None or (isinstance(reason, str) and not reason.strip()):
                    codes.append("reason_required")
                elif not isinstance(reason, str):
                    codes.append("unknown_reason")
                else:
                    base = reason.split(":", 1)[0]
                    if base not in C.REASONS:
                        codes.append("unknown_reason")
                    elif C.REASONS[base] != status:
                        codes.append("reason_status_mismatch")

    return list(dict.fromkeys(codes))

from __future__ import annotations

import decimal
import json
import math
import re

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome
from budongi.team_collection.core.envelope import finalize
from budongi.team_collection.core.missing import classify_value

_ALLOWED_FREQUENCIES = ("daily", "monthly", "quarterly", "yearly")
_NUMERIC_RE = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")


def _is_present(val: object) -> bool:
    """Return True if val is present according to R13."""
    if val is None:
        return False
    if isinstance(val, str) and not val.strip():
        return False
    return True


def normalize_statistic(
    fields: dict,
    *,
    envelope: dict,
    metric_code: str,
    frequency: str,
    unit_code: str,
    value_field: str,
    region_fields: tuple,
    dimensions: dict,
) -> Outcome:
    """Normalize a regional statistic record and return an Outcome."""
    if not isinstance(metric_code, str) or not metric_code.strip():
        raise C.ContractError("invalid_metric_code")

    if frequency not in _ALLOWED_FREQUENCIES:
        raise C.ContractError("invalid_frequency")

    if not isinstance(unit_code, str) or not unit_code.strip():
        raise C.ContractError("invalid_unit_code")

    if not isinstance(value_field, str) or not value_field.strip():
        raise C.ContractError("invalid_value_field")

    if not isinstance(region_fields, (list, tuple)) or not region_fields:
        raise C.ContractError("invalid_region_fields")
    for item in region_fields:
        if not isinstance(item, str) or not item.strip():
            raise C.ContractError("invalid_region_fields")

    if not isinstance(dimensions, dict):
        raise C.ContractError("invalid_dimensions")
    for k in dimensions:
        if not isinstance(k, str):
            raise C.ContractError("invalid_dimensions")
    try:
        dimensions_json = json.dumps(
            dimensions,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError):
        raise C.ContractError("invalid_dimensions")

    record = dict(envelope)
    record.update(fields)

    record["metric_code"] = metric_code
    record["frequency"] = frequency
    record["unit_code"] = unit_code
    record["dimensions_json"] = dimensions_json

    parts: list[str] = []
    for name in region_fields:
        v = fields.get(name)
        if v is None:
            continue
        part = str(v).strip()
        if not part:
            continue
        parts.append(part)

    record["region_path_raw"] = " > ".join(parts) if parts else None
    record["period_key"] = fields.get("period_key")

    val = fields.get(value_field)
    record["value_raw"] = val

    c = classify_value(val)
    if c in ("null", "semantic"):
        value_status = "missing"
        value_decimal = None
    elif isinstance(val, str):
        t = val.strip().replace(",", "")
        if _NUMERIC_RE.fullmatch(t):
            try:
                value_status = "numeric"
                value_decimal = format(decimal.Decimal(t), "f")
            except decimal.InvalidOperation:
                value_status = None
                value_decimal = None
        else:
            value_status = None
            value_decimal = None
    elif isinstance(val, bool):
        value_status = None
        value_decimal = None
    elif isinstance(val, int):
        value_status = "numeric"
        value_decimal = str(val)
    elif isinstance(val, decimal.Decimal):
        if val.is_finite():
            value_status = "numeric"
            value_decimal = format(val, "f")
        else:
            value_status = None
            value_decimal = None
    elif isinstance(val, float):
        if math.isfinite(val):
            value_status = "numeric"
            value_decimal = format(decimal.Decimal(repr(val)), "f")
        else:
            value_status = None
            value_decimal = None
    else:
        value_status = None
        value_decimal = None

    record["value_status"] = value_status
    record["value_decimal"] = value_decimal

    status = "accepted"
    reason: str | None = None

    for req_field in C.REQUIRED_FIELDS["regional_statistic"]:
        if req_field == "value_status":
            continue
        field_val = record.get(req_field)
        if not _is_present(field_val):
            status = "rejected"
            reason = f"missing_required:{req_field}"
            break

    if status == "accepted":
        if value_status is None:
            status = "rejected"
            reason = f"invalid_number:{value_field}"

    final_record = finalize(record, status, reason)
    return Outcome(
        record=final_record,
        status=final_record["validation_status"],
        reason=final_record["validation_reason"],
    )

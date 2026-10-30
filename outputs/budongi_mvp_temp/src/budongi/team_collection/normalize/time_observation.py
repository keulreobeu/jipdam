"""Time-observation normalizer for wide rows and envelopes."""
from __future__ import annotations

import decimal
import re

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome
from budongi.team_collection.core.envelope import finalize
from budongi.team_collection.core.missing import classify_value

_NUMERIC_RE = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")


def _normalize_value(v: object) -> tuple[str | None, str | None]:
    """Normalize raw value v into (value_status, value_decimal)."""
    if classify_value(v) in ("null", "semantic"):
        return "missing", None

    if isinstance(v, str):
        t = v.strip().replace(",", "")
        if _NUMERIC_RE.fullmatch(t) is not None:
            try:
                d = decimal.Decimal(t)
                return "numeric", format(d, "f")
            except (decimal.InvalidOperation, ValueError):
                return None, None
        return None, None

    if isinstance(v, bool):
        return None, None

    if isinstance(v, int):
        return "numeric", str(v)

    if isinstance(v, decimal.Decimal):
        if v.is_finite():
            return "numeric", format(v, "f")
        return None, None

    if isinstance(v, float):
        try:
            d = decimal.Decimal(repr(v))
            if d.is_finite():
                return "numeric", format(d, "f")
        except (decimal.InvalidOperation, ValueError):
            pass
        return None, None

    return None, None


def normalize_observations(
    fields: dict,
    *,
    envelope: dict,
    metrics: list,
    subject_namespace: str,
    subject_field: str,
    observed_at_utc: str,
) -> list:
    """Normalize a wide mapped row into Outcome objects, one per metric."""
    if not isinstance(subject_namespace, str) or subject_namespace.strip() == "":
        raise C.ContractError("invalid_namespace")

    if not isinstance(subject_field, str) or subject_field.strip() == "":
        raise C.ContractError("invalid_subject_field")

    if not isinstance(observed_at_utc, str) or C.UTC_Z_RE.fullmatch(observed_at_utc) is None:
        raise C.ContractError("invalid_observed_at")

    if not isinstance(metrics, (list, tuple)) or len(metrics) == 0:
        raise C.ContractError("invalid_metrics")

    seen_metric_codes: set[str] = set()
    for m in metrics:
        if not isinstance(m, dict):
            raise C.ContractError("invalid_metrics")
        for key in ("metric_code", "source_field", "unit_code"):
            if key not in m:
                raise C.ContractError("invalid_metrics")
            val = m[key]
            if not isinstance(val, str) or val.strip() == "":
                raise C.ContractError("invalid_metrics")
        mc = m["metric_code"]
        if mc in seen_metric_codes:
            raise C.ContractError("invalid_metrics")
        seen_metric_codes.add(mc)

    raw_subject = fields.get(subject_field)
    subject_missing = classify_value(raw_subject) in ("null", "semantic")
    source_subject_id = None if subject_missing else raw_subject

    outcomes: list[Outcome] = []

    for m in metrics:
        v = fields.get(m["source_field"])
        value_status, value_decimal = _normalize_value(v)

        if subject_missing:
            status = "rejected"
            reason: str | None = "missing_required:source_subject_id"
        elif value_status is None:
            status = "rejected"
            reason = f"invalid_number:{m['source_field']}"
        else:
            status = "accepted"
            reason = None

        rec = dict(envelope)
        rec.update(fields)
        rec["metric_code"] = m["metric_code"]
        rec["unit_code"] = m["unit_code"]
        rec["subject_namespace"] = subject_namespace
        rec["source_subject_id"] = source_subject_id
        rec["observed_at_utc"] = observed_at_utc
        rec["value_status"] = value_status
        rec["value_decimal"] = value_decimal
        rec["value_raw"] = v

        final_rec = finalize(rec, status, reason)
        outcomes.append(Outcome(record=final_rec, status=status, reason=reason))

    return outcomes

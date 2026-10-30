from __future__ import annotations
"""Spatial layer feature normalizer."""

import datetime
import math
import re

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome
from budongi.team_collection.core.envelope import finalize

VERDICT_FIELDS: tuple[str, ...] = (
    "verdict",
    "flooded",
    "inundated",
    "affected",
    "in_zone",
    "hazard_level",
    "risk_level",
)
"""Verdict keys an image layer must never carry."""

_EPSG_RE = re.compile(r"\AEPSG:[0-9]+\Z")
_EVENT_DATE_RE = re.compile(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


def _is_present(val: object) -> bool:
    """Return True if val is not None and not a whitespace-only string."""
    if val is None:
        return False
    if isinstance(val, str) and not val.strip():
        return False
    return True


def normalize_feature(
    attrs: dict,
    *,
    envelope: dict,
    layer_id: str,
    representation: str,
    geometry_ref: str | None,
    source_crs: str | None,
    bbox: tuple | None,
    scenario: str | None = None,
    event_date: str | None = None,
) -> Outcome:
    """Normalize one spatial layer feature and return an Outcome."""
    if not isinstance(representation, str) or representation not in C.REPRESENTATIONS:
        raise C.ContractError("invalid_representation")
    if not isinstance(layer_id, str) or not layer_id.strip():
        raise C.ContractError("invalid_layer_id")

    record = dict(envelope)
    record.update(attrs)

    record["layer_id"] = layer_id
    record["representation"] = representation

    record["geometry_ref"] = geometry_ref if _is_present(geometry_ref) else None

    if not _is_present(source_crs):
        record["source_crs"] = "unknown"
        source_crs_valid = True
    else:
        record["source_crs"] = source_crs
        source_crs_valid = isinstance(source_crs, str) and (
            source_crs == "unknown" or bool(_EPSG_RE.fullmatch(source_crs))
        )

    if bbox is None:
        record["bbox"] = None
        bbox_valid = True
    elif not isinstance(bbox, (tuple, list)) or len(bbox) != 4:
        record["bbox"] = None
        bbox_valid = False
    else:
        invalid_elem = False
        for elem in bbox:
            if isinstance(elem, bool) or not isinstance(elem, (int, float)) or not math.isfinite(elem):
                invalid_elem = True
                break
        if invalid_elem:
            record["bbox"] = None
            bbox_valid = False
        else:
            xmin, ymin, xmax, ymax = bbox
            if xmin <= xmax and ymin <= ymax:
                record["bbox"] = [float(xmin), float(ymin), float(xmax), float(ymax)]
                bbox_valid = True
            else:
                record["bbox"] = None
                bbox_valid = False

    record["scenario"] = scenario if _is_present(scenario) else None

    if event_date is None or event_date == "":
        record["event_date"] = None
        event_date_valid = True
    elif isinstance(event_date, str) and bool(_EVENT_DATE_RE.fullmatch(event_date)):
        try:
            datetime.date.fromisoformat(event_date)
            record["event_date"] = event_date
            event_date_valid = True
        except ValueError:
            record["event_date"] = None
            record["event_date_raw"] = event_date
            event_date_valid = False
    else:
        record["event_date"] = None
        record["event_date_raw"] = event_date
        event_date_valid = False

    if representation == "image":
        for field in VERDICT_FIELDS:
            record.pop(field, None)

    if not _is_present(geometry_ref):
        status = "rejected"
        reason = "missing_required:geometry_ref"
    elif not source_crs_valid:
        status = "rejected"
        reason = "invalid_code:source_crs"
    elif not bbox_valid:
        status = "rejected"
        reason = "invalid_geometry:bbox"
    elif not event_date_valid:
        status = "rejected"
        reason = "invalid_date:event_date"
    else:
        status = "accepted"
        reason = None

    finalized = finalize(record, status, reason)
    return Outcome(record=finalized, status=status, reason=reason)

from __future__ import annotations

import decimal
import json
import math
from typing import Any, Iterable

from budongi.team_collection import contract as C


def _freeze(val: Any) -> Any:
    if isinstance(val, dict):
        items = []
        for k, v in val.items():
            items.append((str(k), _freeze(v)))
        items.sort(key=lambda x: x[0])
        return tuple(items)
    if isinstance(val, list):
        return tuple(_freeze(v) for v in val)
    return val


def check_records(lines: Iterable[str], *, manifest: dict, files: dict) -> dict:
    """Check each JSONL line against the contract, manifest and files-by-path map and return problems found."""
    if not isinstance(manifest, dict):
        raise C.ContractError("invalid_manifest")
    if not isinstance(files, dict):
        raise C.ContractError("invalid_files")

    counts = {"lines": 0, "accepted": 0, "rejected": 0, "invalid": 0}
    errors: list[str] = []
    seen_positions: set[tuple] = set()

    for n, line in enumerate(lines, 1):
        counts["lines"] += 1

        if not isinstance(line, str):
            counts["invalid"] += 1
            errors.append(f"invalid_json:{n}")
            continue

        try:
            record = json.loads(line)
        except Exception:
            counts["invalid"] += 1
            errors.append(f"invalid_json:{n}")
            continue

        if not isinstance(record, dict):
            counts["invalid"] += 1
            errors.append(f"invalid_json:{n}")
            continue

        for key in C.ENVELOPE_FIELDS:
            if key not in record:
                errors.append(f"missing_field:{n}:{key}")
        for key in C.LOCATION_FIELDS:
            if key not in record:
                errors.append(f"missing_field:{n}:{key}")

        val_status = record.get("validation_status")
        if val_status == "accepted":
            counts["accepted"] += 1
        elif val_status == "rejected":
            counts["rejected"] += 1
        elif val_status == "excluded":
            errors.append(f"excluded_in_jsonl:{n}")
        else:
            errors.append(f"invalid_status:{n}")

        if val_status == "accepted":
            if record.get("validation_reason") is not None:
                errors.append(f"reason_mismatch:{n}")
        elif val_status == "rejected":
            reason = record.get("validation_reason")
            if not (isinstance(reason, str) and C.REASONS.get(reason.split(":", 1)[0]) == "rejected"):
                errors.append(f"reason_mismatch:{n}")

        if record.get("delivery_schema_version") != C.DELIVERY_SCHEMA_VERSION:
            errors.append(f"schema_version_mismatch:{n}")
        if record.get("quality_status") != C.QUALITY_STATUS:
            errors.append(f"quality_status_mismatch:{n}")

        for k in ("source_id", "batch_id", "mapping_version", "record_type"):
            if record.get(k) != manifest.get(k):
                errors.append(f"id_mismatch:{n}:{k}")

        sha = record.get("source_content_sha256")
        sha_valid = isinstance(sha, str) and bool(C.SHA256_RE.match(sha))
        if not sha_valid:
            errors.append(f"invalid_sha:{n}")

        ref = record.get("source_file_ref")
        ref_is_key = isinstance(ref, str) and (ref in files)
        if not ref_is_key:
            errors.append(f"unknown_file_ref:{n}")
        else:
            if sha_valid:
                file_entry = files[ref]
                expected_sha = file_entry.get("sha256") if isinstance(file_entry, dict) else None
                if sha != expected_sha:
                    errors.append(f"file_sha_mismatch:{n}")

        for key in C.ENVELOPE_FIELDS:
            if key.endswith("_utc"):
                val = record.get(key)
                if val is not None:
                    if not (isinstance(val, str) and bool(C.UTC_Z_RE.match(val))):
                        errors.append(f"invalid_utc:{n}:{key}")

        row_num = record.get("source_row_number")
        feat_id = record.get("source_feature_id")
        is_row_set = (type(row_num) is int and row_num >= 1)
        is_feat_set = (isinstance(feat_id, str) and len(feat_id) > 0)

        valid_pos = False
        if is_row_set and feat_id is None:
            valid_pos = True
        elif is_feat_set and row_num is None:
            valid_pos = True

        if not valid_pos:
            errors.append(f"invalid_position:{n}")
        else:
            pos_key = (
                _freeze(record.get("source_file_ref")),
                _freeze(record.get("source_section")),
                row_num,
                feat_id,
                _freeze(record.get("source_column_number")),
            )
            if pos_key in seen_positions:
                errors.append(f"duplicate_position:{n}")
            else:
                seen_positions.add(pos_key)

        rec_type = record.get("record_type")
        if rec_type not in C.RECORD_TYPES:
            errors.append(f"invalid_record_type:{n}")
        else:
            if val_status == "accepted":
                req_fields = C.REQUIRED_FIELDS.get(rec_type, ())
                for field in req_fields:
                    val = record.get(field)
                    if field not in record or val is None or val == "":
                        errors.append(f"missing_required:{n}:{field}")

            if val_status == "accepted" and rec_type in C.VALUE_TYPES:
                val_status_field = record.get("value_status")
                if val_status_field is not None:
                    if val_status_field not in C.VALUE_STATUSES:
                        errors.append(f"invalid_value_status:{n}")
                    elif val_status_field == "numeric":
                        val_dec = record.get("value_decimal")
                        if not isinstance(val_dec, str):
                            errors.append(f"invalid_value:{n}")
                        else:
                            try:
                                dec = decimal.Decimal(val_dec)
                                if not dec.is_finite():
                                    errors.append(f"invalid_value:{n}")
                            except Exception:
                                errors.append(f"invalid_value:{n}")
                    elif val_status_field == "missing":
                        if record.get("value_decimal") is not None:
                            errors.append(f"invalid_value:{n}")

        lat = record.get("latitude")
        lon = record.get("longitude")
        if (lat is None) != (lon is None):
            errors.append(f"coordinate_pair:{n}")
        elif lat is not None and lon is not None:
            valid_coords = True
            if not (type(lat) in (int, float) and type(lon) in (int, float)):
                valid_coords = False
            elif not (math.isfinite(lat) and math.isfinite(lon)):
                valid_coords = False
            elif record.get("source_crs") != C.WGS84:
                valid_coords = False
            elif record.get("source_axis_order") not in ("x=lon,y=lat", "x=lat,y=lon"):
                valid_coords = False
            elif not (C.KOREA_LAT[0] <= lat <= C.KOREA_LAT[1] and C.KOREA_LON[0] <= lon <= C.KOREA_LON[1]):
                valid_coords = False

            if not valid_coords:
                errors.append(f"coordinate_rule:{n}")

    if manifest.get("normalized_withheld") is True:
        if counts["lines"] > 0:
            errors.append("withheld_lines_present")
    else:
        manifest_counts = manifest.get("counts")
        if isinstance(manifest_counts, dict):
            for k in ("accepted", "rejected"):
                expected = manifest_counts.get(k)
                if type(expected) is int and expected != counts[k]:
                    errors.append(f"{k}_count_mismatch")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "counts": counts,
    }

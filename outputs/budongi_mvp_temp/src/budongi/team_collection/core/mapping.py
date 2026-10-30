from __future__ import annotations

import copy
from datetime import datetime
from decimal import Decimal
import re

from budongi.team_collection import contract as C

_ALLOWED_DOC_KEYS = frozenset({"mapping_version", "record_type", "header_row", "fields", "unmapped"})
_ALLOWED_FIELD_KEYS = frozenset(
    {"target", "source", "type", "required", "formats", "true_values", "false_values", "const"}
)
_ALLOWED_TYPES = frozenset({"text", "code", "int", "decimal", "date", "bool"})
_DATE_DEFAULT_FORMATS = ("%Y-%m-%d", "%Y%m%d", "%Y.%m.%d", "%Y/%m/%d")
_BOOL_DEFAULT_TRUE = ("y", "yes", "true", "1")
_BOOL_DEFAULT_FALSE = ("n", "no", "false", "0")
_INT_RE = re.compile(r"^[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)$")
_DECIMAL_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def compile_mapping(doc: dict) -> dict:
    """Validate a mapping document and return a new normalized mapping dict with defaults filled in."""
    if not isinstance(doc, dict):
        raise C.ContractError("invalid_mapping:not_object")
    if set(doc.keys()) - _ALLOWED_DOC_KEYS:
        raise C.ContractError("invalid_mapping:unknown_key")

    if "mapping_version" not in doc or not isinstance(doc["mapping_version"], str) or doc["mapping_version"] == "":
        raise C.ContractError("invalid_mapping:mapping_version")
    if "record_type" not in doc or (doc["record_type"] not in C.RECORD_TYPES and doc["record_type"] != C.RAW_ONLY):
        raise C.ContractError("invalid_mapping:record_type")

    header_row = 1
    if "header_row" in doc:
        hr = doc["header_row"]
        if isinstance(hr, bool) or not isinstance(hr, int) or hr < 1:
            raise C.ContractError("invalid_mapping:header_row")
        header_row = hr

    if "fields" not in doc or not isinstance(doc["fields"], list):
        raise C.ContractError("invalid_mapping:fields")

    compiled_fields = []
    seen_targets = set()

    for field in doc["fields"]:
        if not isinstance(field, dict):
            raise C.ContractError("invalid_mapping:field")
        if set(field.keys()) - _ALLOWED_FIELD_KEYS:
            raise C.ContractError("invalid_mapping:unknown_key")

        if "target" not in field or not isinstance(field["target"], str) or field["target"] == "":
            raise C.ContractError("invalid_mapping:target")
        target = field["target"]
        if target in seen_targets:
            raise C.ContractError("invalid_mapping:duplicate_target")
        seen_targets.add(target)

        if "type" not in field or field["type"] not in _ALLOWED_TYPES:
            raise C.ContractError("invalid_mapping:type")
        field_type = field["type"]

        has_source = field.get("source") is not None
        has_const = "const" in field
        if (has_source and has_const) or (not has_source and not has_const):
            raise C.ContractError("invalid_mapping:source_const")
        if has_source:
            if not isinstance(field["source"], str) or field["source"] == "":
                raise C.ContractError("invalid_mapping:source")
            source_val = field["source"]
        else:
            source_val = None

        if "required" in field:
            if not isinstance(field["required"], bool):
                raise C.ContractError("invalid_mapping:required")
            is_required = field["required"]
        else:
            is_required = False

        compiled_field = {
            "target": target,
            "source": source_val,
            "type": field_type,
            "required": is_required,
        }

        if has_const:
            const_val = field["const"]
            if isinstance(const_val, (list, dict)):
                const_val = copy.deepcopy(const_val)
            compiled_field["const"] = const_val

        if field_type == "date":
            if "formats" in field:
                fmts = field["formats"]
                if not isinstance(fmts, list) or len(fmts) == 0 or not all(
                    isinstance(f, str) and len(f) > 0 for f in fmts
                ):
                    raise C.ContractError("invalid_mapping:formats")
                compiled_field["formats"] = list(fmts)
            else:
                compiled_field["formats"] = list(_DATE_DEFAULT_FORMATS)
        else:
            if "formats" in field:
                raise C.ContractError("invalid_mapping:formats")

        if field_type == "bool":
            if "true_values" in field:
                tv = field["true_values"]
                if not isinstance(tv, list) or len(tv) == 0 or not all(isinstance(x, str) for x in tv):
                    raise C.ContractError("invalid_mapping:bool_values")
                final_tv = [x.lower() for x in tv]
            else:
                final_tv = list(_BOOL_DEFAULT_TRUE)

            if "false_values" in field:
                fv = field["false_values"]
                if not isinstance(fv, list) or len(fv) == 0 or not all(isinstance(x, str) for x in fv):
                    raise C.ContractError("invalid_mapping:bool_values")
                final_fv = [x.lower() for x in fv]
            else:
                final_fv = list(_BOOL_DEFAULT_FALSE)

            if set(final_tv) & set(final_fv):
                raise C.ContractError("invalid_mapping:bool_values")

            compiled_field["true_values"] = final_tv
            compiled_field["false_values"] = final_fv
        else:
            if "true_values" in field or "false_values" in field:
                raise C.ContractError("invalid_mapping:bool_values")

        compiled_fields.append(compiled_field)

    if "unmapped" in doc:
        unm = doc["unmapped"]
        if not isinstance(unm, list) or not all(isinstance(x, str) and len(x) > 0 for x in unm):
            raise C.ContractError("invalid_mapping:unmapped")
        final_unmapped = list(unm)
    else:
        final_unmapped = []

    field_sources = {f["source"] for f in compiled_fields if f.get("source") is not None}
    if set(final_unmapped) & field_sources:
        raise C.ContractError("invalid_mapping:unmapped_overlap")

    return {
        "mapping_version": doc["mapping_version"],
        "record_type": doc["record_type"],
        "header_row": header_row,
        "fields": compiled_fields,
        "unmapped": final_unmapped,
    }


def apply_mapping(mapping: dict, header: tuple, values: tuple) -> tuple[dict, list[str]]:
    """Convert one row of source values into target values using a compiled mapping."""
    if len(values) != len(header):
        raise C.ContractError("value_count_mismatch")

    for field in mapping["fields"]:
        if "const" not in field:
            src = field["source"]
            if src not in header:
                raise C.ContractError(f"unknown_source_header:{src}")

    record = {}
    errors = []

    for field in mapping["fields"]:
        target = field["target"]
        field_type = field["type"]
        is_required = field.get("required", False)

        if "const" in field:
            const_val = field["const"]
            record[target] = const_val
            if const_val is None and is_required:
                errors.append(f"missing_required:{target}")
            continue

        src = field["source"]
        idx = header.index(src)
        raw_val = values[idx]

        if raw_val is None or (isinstance(raw_val, str) and raw_val.strip() == ""):
            record[target] = None
            if is_required:
                errors.append(f"missing_required:{target}")
            continue

        if field_type in ("text", "code"):
            record[target] = raw_val
        elif field_type == "int":
            s = raw_val.strip()
            if _INT_RE.fullmatch(s):
                record[target] = int(s.replace(",", ""))
            else:
                record[target] = None
                record[target + "_raw"] = raw_val
                errors.append(f"invalid_number:{target}")
        elif field_type == "decimal":
            s = raw_val.strip().replace(",", "")
            if _DECIMAL_RE.fullmatch(s):
                try:
                    record[target] = format(Decimal(s), "f")
                except Exception:
                    record[target] = None
                    record[target + "_raw"] = raw_val
                    errors.append(f"invalid_number:{target}")
            else:
                record[target] = None
                record[target + "_raw"] = raw_val
                errors.append(f"invalid_number:{target}")
        elif field_type == "date":
            s = raw_val.strip()
            parsed_date = None
            for fmt in field["formats"]:
                try:
                    dt = datetime.strptime(s, fmt)
                    parsed_date = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
                    break
                except ValueError:
                    continue
            if parsed_date is not None:
                record[target] = parsed_date
            else:
                record[target] = None
                record[target + "_raw"] = raw_val
                errors.append(f"invalid_date:{target}")
        elif field_type == "bool":
            s = raw_val.strip().lower()
            if s in field["true_values"]:
                record[target] = True
            elif s in field["false_values"]:
                record[target] = False
            else:
                record[target] = None
                record[target + "_raw"] = raw_val
                errors.append(f"invalid_code:{target}")

    return record, errors


def header_coverage(mapping: dict, headers: tuple) -> dict:
    """Report which headers are mapped, declared unmapped or unknown, and which mapped sources are missing."""
    field_sources = {f["source"] for f in mapping["fields"] if f.get("source") is not None}
    unmapped_set = set(mapping.get("unmapped", []))

    mapped = []
    mapped_seen = set()

    unmapped_declared = []
    unmapped_declared_seen = set()

    unknown = []
    unknown_seen = set()

    for h in headers:
        if h in field_sources:
            if h not in mapped_seen:
                mapped_seen.add(h)
                mapped.append(h)
        elif h in unmapped_set:
            if h not in unmapped_declared_seen:
                unmapped_declared_seen.add(h)
                unmapped_declared.append(h)
        else:
            if h not in unknown_seen:
                unknown_seen.add(h)
                unknown.append(h)

    headers_set = set(headers)
    missing = []
    missing_seen = set()

    for field in mapping["fields"]:
        src = field.get("source")
        if src is not None and src not in headers_set:
            if src not in missing_seen:
                missing_seen.add(src)
                missing.append(src)

    complete = len(unknown) == 0 and len(missing) == 0

    return {
        "mapped": mapped,
        "unmapped_declared": unmapped_declared,
        "unknown": unknown,
        "missing": missing,
        "complete": complete,
    }

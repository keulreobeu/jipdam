"""Build and check the team_collection_v1 schema.json document."""
from __future__ import annotations

import copy

from budongi.team_collection import contract as C

_SCHEMA_KEYS = (
    "delivery_schema_version", "source_id", "record_type", "mapping_version", "format",
    "columns", "source_file", "source_field_map", "unit_conversion", "missing_markers",
    "identifier", "status_rules", "region_code_definition", "coordinates", "unmapped_fields",
)
_DESCRIPTIVE_KEYS = (
    "format", "unit_conversion", "missing_markers", "identifier", "status_rules",
    "region_code_definition", "coordinates",
)
_COLUMN_KEYS = frozenset({"name", "type", "nullable", "unit", "description", "required_when"})


def _err(code: str) -> C.ContractError:
    """Return a ContractError carrying the given code."""
    return C.ContractError(code)


def _nonblank(value: object) -> bool:
    """Tell whether value is a str with non-whitespace content."""
    return isinstance(value, str) and bool(value.strip())


def _str_or_none(value: object) -> bool:
    """Tell whether value is a str or None."""
    return value is None or isinstance(value, str)


def _check_column(col: object) -> None:
    """Raise invalid_schema:column unless col is a valid column dict."""
    if not isinstance(col, dict):
        raise _err("invalid_schema:column")
    for key in col:
        if not isinstance(key, str) or key not in _COLUMN_KEYS:
            raise _err("invalid_schema:column")
    if not _nonblank(col.get("name")) or not _nonblank(col.get("type")):
        raise _err("invalid_schema:column")
    if "nullable" in col and not isinstance(col["nullable"], bool):
        raise _err("invalid_schema:column")
    for key in ("unit", "description", "required_when"):
        if key in col and not _str_or_none(col[key]):
            raise _err("invalid_schema:column")


def _build_columns(columns: object) -> list[dict]:
    """Validate columns and return normalized new column dicts."""
    if not isinstance(columns, (list, tuple)):
        raise _err("invalid_schema:columns")
    for col in columns:
        _check_column(col)
    names: set[str] = set()
    for col in columns:
        if col["name"] in names:
            raise _err("invalid_schema:duplicate_column")
        names.add(col["name"])
    return [
        {
            "name": col["name"],
            "type": col["type"],
            "nullable": col.get("nullable", True),
            "unit": col.get("unit"),
            "description": col.get("description"),
            "required_when": col.get("required_when"),
        }
        for col in columns
    ]


def _build_field_map(field_map: object) -> dict:
    """Validate field_map and return a new dict with the same items."""
    if not isinstance(field_map, dict):
        raise _err("invalid_schema:field_map")
    for key, value in field_map.items():
        if not isinstance(key, str) or key == "":
            raise _err("invalid_schema:field_map")
        if not _str_or_none(value):
            raise _err("invalid_schema:field_map")
    return dict(field_map)


def _build_unmapped(unmapped: object, field_map: dict) -> list[str]:
    """Validate unmapped against itself and field_map; return a new list."""
    if not isinstance(unmapped, (list, tuple)):
        raise _err("invalid_schema:unmapped")
    if not all(isinstance(item, str) for item in unmapped):
        raise _err("invalid_schema:unmapped")
    if len(set(unmapped)) != len(unmapped):
        raise _err("invalid_schema:unmapped")
    mapped_headers = {v for v in field_map.values() if isinstance(v, str)}
    for item in unmapped:
        if item in mapped_headers:
            raise _err("invalid_schema:unmapped_conflict")
    return list(unmapped)


def _check_extra(extra: object) -> dict:
    """Validate extra and return it as a dict (empty when None)."""
    if extra is None:
        return {}
    if not isinstance(extra, dict):
        raise _err("invalid_schema:extra")
    for key in extra:
        if not isinstance(key, str) or key not in _DESCRIPTIVE_KEYS:
            raise _err("invalid_schema:extra_key")
    return extra


def build_schema(*, source_id: str, record_type: str, mapping_version: str, columns: list[dict],
                 source_file: str, field_map: dict, unmapped: list[str],
                 extra: dict | None = None) -> dict:
    """Validate the inputs and return the 15-key ordered schema document."""
    if not isinstance(source_id, str) or C.SOURCE_ID_RE.fullmatch(source_id) is None:
        raise _err("invalid_schema:source_id")
    if not isinstance(record_type, str) or not (
            record_type in C.RECORD_TYPES or record_type == C.RAW_ONLY):
        raise _err("invalid_schema:record_type")
    if not _nonblank(mapping_version):
        raise _err("invalid_schema:mapping_version")
    out_columns = _build_columns(columns)
    if not _nonblank(source_file):
        raise _err("invalid_schema:source_file")
    out_map = _build_field_map(field_map)
    out_unmapped = _build_unmapped(unmapped, out_map)
    extra_dict = _check_extra(extra)

    result: dict = {
        "delivery_schema_version": C.DELIVERY_SCHEMA_VERSION,
        "source_id": source_id,
        "record_type": record_type,
        "mapping_version": mapping_version,
    }
    descriptive = {key: copy.deepcopy(extra_dict[key]) if key in extra_dict else None
                   for key in _DESCRIPTIVE_KEYS}
    result["format"] = descriptive["format"]
    result["columns"] = out_columns
    result["source_file"] = source_file
    result["source_field_map"] = out_map
    result["unit_conversion"] = descriptive["unit_conversion"]
    result["missing_markers"] = descriptive["missing_markers"]
    result["identifier"] = descriptive["identifier"]
    result["status_rules"] = descriptive["status_rules"]
    result["region_code_definition"] = descriptive["region_code_definition"]
    result["coordinates"] = descriptive["coordinates"]
    result["unmapped_fields"] = out_unmapped
    return result


def missing_keys(schema: dict) -> list[str]:
    """Return the required schema keys absent, None or blank in schema, in schema order."""
    if not isinstance(schema, dict):
        raise _err("invalid_schema:not_dict")
    missing: list[str] = []
    for key in _SCHEMA_KEYS:
        if key not in schema:
            missing.append(key)
            continue
        value = schema[key]
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(key)
    return missing

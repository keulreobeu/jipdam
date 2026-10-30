from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from budongi.team_collection import contract as C


def _classify_value(val: object, marker_set: set[str]) -> str:
    """Classify a row value as null, semantic, or present."""
    if val is None:
        return "null"
    if isinstance(val, str) and val.strip() in marker_set:
        return "semantic"
    return "present"


def _present_text(val: object) -> str:
    """Return the present text representation of a value."""
    if isinstance(val, str):
        return val
    return str(val)


def _parse_coord(val: object, marker_set: set[str]) -> float | None:
    """Parse a coordinate value to float if valid and finite, else None."""
    if isinstance(val, bool):
        return None
    if _classify_value(val, marker_set) != "present":
        return None
    text = _present_text(val)
    try:
        f = float(text)
    except (ValueError, TypeError):
        return None
    if not math.isfinite(f):
        return None
    return f


def _rows_identical(r1: dict, r2: dict) -> bool:
    """Check if two row dicts have identical keys and typed values."""
    if len(r1) != len(r2):
        return False
    for k, v1 in r1.items():
        if k not in r2:
            return False
        v2 = r2[k]
        if type(v1) is not type(v2) or v1 != v2:
            return False
    return True


def _row_hash(r: dict) -> int:
    """Compute an order-independent hash of keys and typed values."""
    h = len(r)
    for k, v in r.items():
        item_h = (hash(k) * 31 + hash(type(v))) & 0xFFFFFFFF
        try:
            item_h = (item_h * 31 + hash(v)) & 0xFFFFFFFF
        except TypeError:
            pass
        h = (h + item_h) & 0xFFFFFFFF
    return h


def recount_rows(
    rows: Iterable[dict],
    *,
    columns: Sequence[str],
    pk: Sequence[str],
    address_cols: Sequence[str],
    coord_cols: tuple[str, str] | None,
    markers: Iterable[str],
) -> dict:
    """Recount column missingness, distinct values, duplicates, address, and coordinates."""
    seen_columns: set[str] = set()
    for col in columns:
        if col in seen_columns:
            raise C.ContractError("duplicate_column")
        seen_columns.add(col)

    if coord_cols is not None:
        if (
            not isinstance(coord_cols, tuple)
            or len(coord_cols) != 2
            or not isinstance(coord_cols[0], str)
            or not isinstance(coord_cols[1], str)
        ):
            raise C.ContractError("invalid_coord_cols")

    marker_set: set[str] = set()
    for m in markers:
        if not isinstance(m, str):
            raise C.ContractError("invalid_marker")
        marker_set.add(m)

    col_stats: dict[str, dict[str, object]] = {
        col: {"null": 0, "semantic": 0, "present": 0, "distinct": set()}
        for col in columns
    }

    total = 0
    full_duplicates = 0
    pk_duplicates = 0
    pk_missing = 0
    address_present = 0
    coord_present = 0
    coord_valid = 0

    seen_rows: dict[int, list[dict]] = {}
    seen_pks: set[tuple[str, ...]] = set()

    for row in rows:
        if not isinstance(row, dict):
            raise C.ContractError("invalid_row")
        total += 1

        for col in columns:
            val = row.get(col)
            classification = _classify_value(val, marker_set)
            if classification == "null":
                col_stats[col]["null"] += 1
            elif classification == "semantic":
                col_stats[col]["semantic"] += 1
            else:
                col_stats[col]["present"] += 1
                col_stats[col]["distinct"].add(_present_text(val))

        rh = _row_hash(row)
        bucket = seen_rows.setdefault(rh, [])
        is_dup = False
        for earlier in bucket:
            if _rows_identical(row, earlier):
                is_dup = True
                break
        if is_dup:
            full_duplicates += 1
        else:
            bucket.append(row)

        if pk:
            pk_has_missing = False
            pk_texts: list[str] = []
            for col in pk:
                val = row.get(col)
                if _classify_value(val, marker_set) != "present":
                    pk_has_missing = True
                    break
                pk_texts.append(_present_text(val))

            if pk_has_missing:
                pk_missing += 1
            else:
                pk_key = tuple(pk_texts)
                if pk_key in seen_pks:
                    pk_duplicates += 1
                else:
                    seen_pks.add(pk_key)

        if address_cols:
            for col in address_cols:
                if _classify_value(row.get(col), marker_set) == "present":
                    address_present += 1
                    break

        if coord_cols is not None:
            x_val = _parse_coord(row.get(coord_cols[0]), marker_set)
            y_val = _parse_coord(row.get(coord_cols[1]), marker_set)
            if x_val is not None and y_val is not None:
                coord_present += 1
                if (
                    C.KOREA_LON[0] <= x_val <= C.KOREA_LON[1]
                    and C.KOREA_LAT[0] <= y_val <= C.KOREA_LAT[1]
                ):
                    coord_valid += 1

    result_columns: dict[str, dict[str, int]] = {}
    for col in columns:
        entry = col_stats[col]
        null_cnt: int = entry["null"]
        semantic_cnt: int = entry["semantic"]
        result_columns[col] = {
            "total": total,
            "null": null_cnt,
            "semantic": semantic_cnt,
            "missing": null_cnt + semantic_cnt,
            "present": entry["present"],
            "distinct": len(entry["distinct"]),
        }

    return {
        "total": total,
        "columns": result_columns,
        "full_duplicates": full_duplicates,
        "pk_duplicates": pk_duplicates,
        "pk_missing": pk_missing,
        "address_present": address_present,
        "coord_present": coord_present,
        "coord_valid": coord_valid,
    }

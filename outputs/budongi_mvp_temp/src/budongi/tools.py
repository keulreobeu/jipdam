"""Three allowlisted, validated data tools. The model never receives SQL access."""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any

TOOL_SCHEMA_VERSION = "tools_v1"
MAX_ROWS = 20
TOOL_SPECS: list[dict[str, Any]] = [
    {"type": "function", "function": {"name": "search_apartments", "description": "Find apartments by district and latest valid transaction price/area.",
     "parameters": {"type": "object", "properties": {
         "district": {"type": "string"}, "max_price_krw": {"type": "integer", "minimum": 1},
         "area_sqm": {"type": "number", "exclusiveMinimum": 0},
         "built_year_min": {"type": "integer", "minimum": 1800, "maximum": 2023},
         "limit": {"type": "integer", "minimum": 1, "maximum": MAX_ROWS}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "search_transactions", "description": "Find effective valid/corrected actual transactions, ordered by contract date.",
     "parameters": {"type": "object", "properties": {
         "apartment_id": {"type": "string"}, "contract_date_from": {"type": "string", "format": "date"},
         "contract_date_to": {"type": "string", "format": "date"},
         "max_price_krw": {"type": "integer", "minimum": 1},
         "area_sqm": {"type": "number", "exclusiveMinimum": 0},
         "limit": {"type": "integer", "minimum": 1, "maximum": MAX_ROWS}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_apartment_detail", "description": "Return one apartment, its location, and its latest effective transaction.",
     "parameters": {"type": "object", "properties": {"apartment_id": {"type": "string"}},
                    "required": ["apartment_id"], "additionalProperties": False}}},
]

_FIELDS = {
    "search_apartments": {"district", "max_price_krw", "area_sqm", "built_year_min", "limit"},
    "search_transactions": {"apartment_id", "contract_date_from", "contract_date_to", "max_price_krw", "area_sqm", "limit"},
    "get_apartment_detail": {"apartment_id"},
}


def _validate(tool: str, arguments: Any) -> dict[str, Any]:
    if tool not in _FIELDS:
        raise ValueError(f"Tool is not allowed: {tool}")
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object")
    extra = set(arguments) - _FIELDS[tool]
    if extra:
        raise ValueError(f"Unknown arguments: {sorted(extra)}")
    if tool == "get_apartment_detail" and not arguments.get("apartment_id"):
        raise ValueError("apartment_id is required")
    for key in ("district", "apartment_id"):
        if key in arguments and (not isinstance(arguments[key], str) or not arguments[key].strip() or len(arguments[key]) > 100):
            raise ValueError(f"{key} must be a non-empty string of at most 100 characters")
    for key in ("max_price_krw", "built_year_min", "limit"):
        if key in arguments and (type(arguments[key]) is not int or arguments[key] <= 0):
            raise ValueError(f"{key} must be a positive integer")
    if arguments.get("limit", 1) > MAX_ROWS:
        raise ValueError(f"limit must be <= {MAX_ROWS}")
    if "built_year_min" in arguments and not 1800 <= arguments["built_year_min"] <= 2023:
        raise ValueError("built_year_min is outside the historical range")
    if "area_sqm" in arguments and (type(arguments["area_sqm"]) not in (int, float) or not 0 < arguments["area_sqm"] <= 1000):
        raise ValueError("area_sqm must be between 0 and 1000")
    for key in ("contract_date_from", "contract_date_to"):
        if key in arguments:
            if not isinstance(arguments[key], str):
                raise ValueError(f"{key} must be ISO date text")
            date.fromisoformat(arguments[key])
    if arguments.get("contract_date_from", "") > arguments.get("contract_date_to", "9999"):
        raise ValueError("contract_date_from exceeds contract_date_to")
    return arguments


def _effective_transactions_sql() -> str:
    # Same source_id denotes versions of one reported transaction. Latest version wins.
    return """
    WITH revised AS (
      SELECT t.*, ROW_NUMBER() OVER (
        PARTITION BY t.snapshot_id, t.source, t.source_id
        ORDER BY t.valid_date DESC, COALESCE(t.changed_date, '') DESC, t.transaction_id DESC
      ) AS revision_rank
      FROM transactions t WHERE t.snapshot_id = ?
    ), effective AS (
      SELECT * FROM revised WHERE revision_rank = 1 AND status IN ('valid', 'corrected')
    )
    """


def _snapshot(connection: sqlite3.Connection, snapshot_id: str) -> dict[str, Any]:
    row = connection.execute("SELECT snapshot_id, snapshot_date, schema_version FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown snapshot: {snapshot_id}")
    return dict(row)


def execute_tool(connection: sqlite3.Connection, snapshot_id: str, tool: str, arguments: Any) -> dict[str, Any]:
    args = _validate(tool, arguments)
    snapshot = _snapshot(connection, snapshot_id)
    limit = args.get("limit", MAX_ROWS)
    if tool == "search_transactions":
        sql = _effective_transactions_sql() + """
        SELECT transaction_id, apartment_id, contract_date, reported_date, changed_date,
               price_krw, area_sqm, floor, status, source, source_id, valid_date
        FROM effective WHERE 1=1
        """
        params: list[Any] = [snapshot_id]
        if "apartment_id" in args:
            sql += " AND apartment_id = ?"
            params.append(args["apartment_id"])
        if "contract_date_from" in args:
            sql += " AND contract_date >= ?"
            params.append(args["contract_date_from"])
        if "contract_date_to" in args:
            sql += " AND contract_date <= ?"
            params.append(args["contract_date_to"])
        if "max_price_krw" in args:
            sql += " AND price_krw <= ?"
            params.append(args["max_price_krw"])
        if "area_sqm" in args:
            sql += " AND ABS(area_sqm - ?) <= 0.5"
            params.append(args["area_sqm"])
        sql += " ORDER BY contract_date DESC, transaction_id DESC LIMIT ?"
        params.append(limit)
        rows = [dict(row) for row in connection.execute(sql, params)]
    elif tool == "search_apartments":
        sql = _effective_transactions_sql() + """
        , ranked AS (
          SELECT e.*, ROW_NUMBER() OVER (
            PARTITION BY e.apartment_id ORDER BY e.contract_date DESC, e.transaction_id DESC
          ) AS apartment_rank FROM effective e
        )
        SELECT a.apartment_id, a.name, a.address, a.district, a.built_year,
               a.source, a.source_id, a.valid_date,
               t.transaction_id, t.contract_date, t.price_krw, t.area_sqm,
               t.status AS transaction_status, t.valid_date AS transaction_valid_date,
               t.source AS transaction_source, t.source_id AS transaction_source_id
        FROM apartments a LEFT JOIN ranked t ON t.snapshot_id = a.snapshot_id
          AND t.apartment_id = a.apartment_id AND t.apartment_rank = 1
        WHERE a.snapshot_id = ?
        """
        params = [snapshot_id, snapshot_id]
        if "district" in args:
            sql += " AND a.district = ?"
            params.append(args["district"])
        if "built_year_min" in args:
            sql += " AND a.built_year >= ?"
            params.append(args["built_year_min"])
        if "max_price_krw" in args:
            sql += " AND t.price_krw <= ?"
            params.append(args["max_price_krw"])
        if "area_sqm" in args:
            sql += " AND ABS(t.area_sqm - ?) <= 0.5"
            params.append(args["area_sqm"])
        sql += " ORDER BY a.apartment_id LIMIT ?"
        params.append(limit)
        rows = [dict(row) for row in connection.execute(sql, params)]
    else:
        sql = _effective_transactions_sql() + """
        , ranked AS (
          SELECT e.*, ROW_NUMBER() OVER (
            PARTITION BY e.apartment_id ORDER BY e.contract_date DESC, e.transaction_id DESC
          ) AS apartment_rank FROM effective e
        )
        SELECT a.*, l.lat, l.lon, l.station_name, l.station_distance_m,
               l.valid_date AS location_valid_date,
               l.source AS location_source, l.source_id AS location_source_id,
               t.transaction_id, t.contract_date, t.price_krw, t.area_sqm,
               t.status AS transaction_status, t.valid_date AS transaction_valid_date,
               t.source AS transaction_source, t.source_id AS transaction_source_id
        FROM apartments a
        LEFT JOIN locations l ON l.snapshot_id = a.snapshot_id AND l.apartment_id = a.apartment_id
        LEFT JOIN ranked t ON t.snapshot_id = a.snapshot_id AND t.apartment_id = a.apartment_id
          AND t.apartment_rank = 1
        WHERE a.snapshot_id = ? AND a.apartment_id = ? LIMIT 1
        """
        rows = [dict(row) for row in connection.execute(sql, (snapshot_id, snapshot_id, args["apartment_id"]))]
    return {"tool": tool, "arguments": args, "snapshot": snapshot, "row_count": len(rows), "rows": rows}

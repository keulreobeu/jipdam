"""Immutable snapshot imports and parameterized SQLite serving database."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from .legacy import parse_address, read_legacy_csv

SCHEMA_VERSION = "serving_v1"
HISTORICAL_CUTOFF = date(2023, 12, 31)

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY, snapshot_date TEXT NOT NULL,
    created_at TEXT NOT NULL, source_manifest TEXT NOT NULL, schema_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS apartments (
    snapshot_id TEXT NOT NULL, apartment_id TEXT NOT NULL, name TEXT NOT NULL,
    address TEXT, province TEXT, district TEXT, neighborhood TEXT,
    built_year INTEGER, source TEXT NOT NULL, source_id TEXT NOT NULL,
    valid_date TEXT NOT NULL, ingested_at TEXT NOT NULL,
    PRIMARY KEY(snapshot_id, apartment_id),
    FOREIGN KEY(snapshot_id) REFERENCES snapshots(snapshot_id)
);
CREATE TABLE IF NOT EXISTS locations (
    snapshot_id TEXT NOT NULL, apartment_id TEXT NOT NULL,
    lat REAL, lon REAL, station_name TEXT, station_distance_m REAL,
    source TEXT NOT NULL, source_id TEXT NOT NULL, valid_date TEXT NOT NULL,
    PRIMARY KEY(snapshot_id, apartment_id),
    FOREIGN KEY(snapshot_id, apartment_id) REFERENCES apartments(snapshot_id, apartment_id)
);
CREATE TABLE IF NOT EXISTS facilities (
    snapshot_id TEXT NOT NULL, facility_id TEXT NOT NULL, apartment_id TEXT NOT NULL,
    category TEXT NOT NULL, name TEXT, distance_m REAL,
    source TEXT NOT NULL, source_id TEXT NOT NULL, valid_date TEXT NOT NULL,
    PRIMARY KEY(snapshot_id, facility_id),
    FOREIGN KEY(snapshot_id, apartment_id) REFERENCES apartments(snapshot_id, apartment_id)
);
CREATE TABLE IF NOT EXISTS transactions (
    snapshot_id TEXT NOT NULL, transaction_id TEXT NOT NULL, apartment_id TEXT NOT NULL,
    contract_date TEXT NOT NULL, reported_date TEXT, changed_date TEXT,
    price_krw INTEGER NOT NULL, area_sqm REAL NOT NULL, floor INTEGER,
    status TEXT NOT NULL CHECK(status IN ('valid','canceled','corrected')),
    source TEXT NOT NULL, source_id TEXT NOT NULL, valid_date TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY(snapshot_id, transaction_id),
    FOREIGN KEY(snapshot_id, apartment_id) REFERENCES apartments(snapshot_id, apartment_id)
);
CREATE INDEX IF NOT EXISTS ix_apartments_district ON apartments(snapshot_id, district);
CREATE INDEX IF NOT EXISTS ix_transactions_lookup ON transactions(snapshot_id, apartment_id, contract_date);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    return connection


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iso_date(value: str, field: str, cutoff: date) -> str:
    parsed = date.fromisoformat(value)
    if parsed > cutoff:
        raise ValueError(f"{field} exceeds snapshot date: {value}")
    return parsed.isoformat()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _required(row: dict[str, str], names: tuple[str, ...]) -> None:
    missing = [name for name in names if not row.get(name, "").strip()]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def import_snapshot(
    connection: sqlite3.Connection, *, snapshot_id: str, snapshot_date: str,
    apartments_csv: Path, transactions_csv: Path,
) -> dict[str, int]:
    """Import normalized CSVs once. A snapshot ID is never overwritten."""
    cutoff = date.fromisoformat(snapshot_date)
    if cutoff > HISTORICAL_CUTOFF:
        raise ValueError("Historical importer only accepts snapshots through 2023-12-31")
    apartments = _rows(apartments_csv)
    transactions = _rows(transactions_csv)
    now = datetime.now(timezone.utc).isoformat()
    manifest = {str(path.name): _sha256(path) for path in (apartments_csv, transactions_csv)}
    with connection:
        connection.execute(
            "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?)",
            (snapshot_id, snapshot_date, now, json.dumps(manifest, sort_keys=True), SCHEMA_VERSION),
        )
        for row in apartments:
            _required(row, ("apartment_id", "name", "source", "source_id", "valid_date"))
            valid_date = _iso_date(row["valid_date"], "apartment.valid_date", cutoff)
            address = row.get("address") or None
            parsed = parse_address(address)
            connection.execute(
                """INSERT INTO apartments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (snapshot_id, row["apartment_id"], row["name"], address,
                 row.get("province") or parsed["province"], row.get("district") or parsed["district"],
                 row.get("neighborhood") or parsed["neighborhood"],
                 int(row["built_year"]) if row.get("built_year") else None,
                 row["source"], row["source_id"], valid_date, now),
            )
            if row.get("lat") or row.get("lon") or row.get("station_distance_m"):
                connection.execute(
                    "INSERT INTO locations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (snapshot_id, row["apartment_id"], float(row["lat"]) if row.get("lat") else None,
                     float(row["lon"]) if row.get("lon") else None, row.get("station_name") or None,
                     float(row["station_distance_m"]) if row.get("station_distance_m") else None,
                     row["source"], row["source_id"], valid_date),
                )
        for row in transactions:
            _required(row, ("transaction_id", "apartment_id", "contract_date", "price_krw",
                            "area_sqm", "status", "source", "source_id", "valid_date"))
            status = row["status"]
            if status not in {"valid", "canceled", "corrected"}:
                raise ValueError(f"Invalid transaction status: {status}")
            for field in ("contract_date", "valid_date", "reported_date", "changed_date"):
                if row.get(field):
                    _iso_date(row[field], field, cutoff)
            price = int(row["price_krw"])
            area = float(row["area_sqm"])
            if price <= 0 or area <= 0:
                raise ValueError("Transaction price and area must be positive")
            connection.execute(
                "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (snapshot_id, row["transaction_id"], row["apartment_id"], row["contract_date"],
                 row.get("reported_date") or None, row.get("changed_date") or None,
                 price, area, int(row["floor"]) if row.get("floor") else None, status,
                 row["source"], row["source_id"], row["valid_date"], now),
            )
    return {"apartments": len(apartments), "transactions": len(transactions)}


def inspect_legacy(path: Path) -> dict[str, object]:
    """Report reusable fields; do not relabel supply price as transactions."""
    rows, encoding = read_legacy_csv(path)
    fields = set(rows[0]) if rows else set()
    return {
        "rows": len(rows), "encoding": encoding,
        "available_fields": sorted(fields & {"문서ID", "아파트명", "법정동주소", "전용면적", "공급액(만원)",
                                        "입주예정연도", "위도", "경도", "지하철역_거리"}),
        "note": "공급액(만원)은 실거래가가 아니므로 transactions로 가져오지 않습니다.",
    }

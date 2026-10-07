"""Immutable, source-traceable storage for the separate rental data path.

Rows accepted here are normalized inputs. The MOLIT XML reader deliberately
does not convert source values until the detailed field and unit contract has
been checked. No function in this module downloads data or infers apartment
identity from names, addresses, or matching prices.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

RENTAL_SCHEMA_VERSION = "rental_v1"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_FACILITY_CATEGORIES = {"station", "supermarket", "park", "hospital"}
_CREDENTIAL_FIELDS = {"servicekey", "apikey", "authorization", "token", "accesstoken",
                      "refreshtoken", "clientsecret", "password"}
_RENTAL_TABLES = {"rental_schema", "rental_snapshots", "rental_observations",
                  "rental_complexes", "rental_facilities", "rental_facility_coverage",
                  "rental_observation_matches"}
_IMMUTABLE_TABLES = _RENTAL_TABLES - {"rental_schema"}
_SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS rental_schema (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1), schema_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rental_snapshots (
    snapshot_id TEXT PRIMARY KEY, snapshot_date TEXT NOT NULL, created_at_utc TEXT NOT NULL,
    source_manifest_json TEXT NOT NULL, schema_version TEXT NOT NULL,
    quality_status TEXT NOT NULL CHECK (quality_status IN ('synthetic_only','source_unverified')),
    sealed INTEGER NOT NULL CHECK (sealed IN (0, 1))
);
CREATE TABLE IF NOT EXISTS rental_observations (
    snapshot_id TEXT NOT NULL, observation_id TEXT NOT NULL, source TEXT NOT NULL,
    source_record_id TEXT, source_file_ref TEXT NOT NULL, source_content_sha256 TEXT NOT NULL,
    source_row_number INTEGER NOT NULL CHECK (source_row_number > 0), sgg_cd TEXT,
    legal_dong TEXT, apartment_name TEXT NOT NULL, jibun TEXT, contract_date TEXT NOT NULL,
    rental_type TEXT NOT NULL CHECK (rental_type IN ('jeonse','wolse')),
    deposit_krw INTEGER NOT NULL CHECK (deposit_krw >= 0),
    monthly_rent_krw INTEGER NOT NULL CHECK (monthly_rent_krw >= 0),
    area_sqm REAL NOT NULL CHECK (area_sqm > 0), floor INTEGER, build_year INTEGER,
    contract_term TEXT, contract_type TEXT, renewal_right_used TEXT,
    previous_deposit_krw INTEGER CHECK (previous_deposit_krw IS NULL OR previous_deposit_krw >= 0),
    previous_monthly_rent_krw INTEGER CHECK (previous_monthly_rent_krw IS NULL OR previous_monthly_rent_krw >= 0),
    source_status TEXT, ingested_at_utc TEXT NOT NULL, raw_payload_json TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, observation_id),
    FOREIGN KEY (snapshot_id) REFERENCES rental_snapshots(snapshot_id)
);
CREATE INDEX IF NOT EXISTS ix_rental_observations_lookup
    ON rental_observations(snapshot_id, sgg_cd, contract_date, apartment_name);
CREATE TABLE IF NOT EXISTS rental_complexes (
    snapshot_id TEXT NOT NULL, complex_id TEXT NOT NULL, name TEXT NOT NULL, sgg_cd TEXT NOT NULL,
    legal_dong TEXT, jibun TEXT, latitude REAL, longitude REAL, identity_evidence TEXT NOT NULL,
    source TEXT NOT NULL, source_record_id TEXT, source_file_ref TEXT NOT NULL,
    source_content_sha256 TEXT NOT NULL, source_row_number INTEGER NOT NULL CHECK (source_row_number > 0),
    ingested_at_utc TEXT NOT NULL, raw_payload_json TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, complex_id),
    FOREIGN KEY (snapshot_id) REFERENCES rental_snapshots(snapshot_id),
    CHECK ((latitude IS NULL AND longitude IS NULL) OR
           (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180))
);
CREATE TABLE IF NOT EXISTS rental_facilities (
    snapshot_id TEXT NOT NULL, facility_observation_id TEXT NOT NULL, source_facility_id TEXT,
    category TEXT NOT NULL CHECK (category IN ('station','supermarket','park','hospital')),
    name TEXT NOT NULL, sgg_cd TEXT, latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180), source TEXT NOT NULL,
    source_file_ref TEXT NOT NULL, source_content_sha256 TEXT NOT NULL,
    source_row_number INTEGER NOT NULL CHECK (source_row_number > 0), ingested_at_utc TEXT NOT NULL,
    raw_payload_json TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, facility_observation_id),
    FOREIGN KEY (snapshot_id) REFERENCES rental_snapshots(snapshot_id)
);
CREATE TABLE IF NOT EXISTS rental_facility_coverage (
    snapshot_id TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('station','supermarket','park','hospital')),
    sgg_cd TEXT NOT NULL, coverage_status TEXT NOT NULL CHECK (coverage_status IN ('complete','partial','unknown')),
    covered_feature_count INTEGER CHECK (covered_feature_count IS NULL OR covered_feature_count >= 0),
    source TEXT NOT NULL, source_record_id TEXT, source_file_ref TEXT NOT NULL,
    source_content_sha256 TEXT NOT NULL, checked_at_utc TEXT NOT NULL, raw_payload_json TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, category, sgg_cd),
    FOREIGN KEY (snapshot_id) REFERENCES rental_snapshots(snapshot_id)
);
CREATE TABLE IF NOT EXISTS rental_observation_matches (
    snapshot_id TEXT NOT NULL, observation_id TEXT NOT NULL, complex_id TEXT NOT NULL,
    review_status TEXT NOT NULL CHECK (review_status IN ('pending','confirmed','rejected')),
    match_basis TEXT NOT NULL, evidence TEXT, reviewed_by TEXT, reviewed_at_utc TEXT,
    PRIMARY KEY (snapshot_id, observation_id, complex_id),
    FOREIGN KEY (snapshot_id, observation_id)
        REFERENCES rental_observations(snapshot_id, observation_id),
    FOREIGN KEY (snapshot_id, complex_id) REFERENCES rental_complexes(snapshot_id, complex_id),
    CHECK (review_status != 'confirmed' OR
           (length(trim(evidence)) > 0 AND length(trim(reviewed_by)) > 0 AND reviewed_at_utc IS NOT NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_rental_observation_confirmed_match
    ON rental_observation_matches(snapshot_id, observation_id) WHERE review_status = 'confirmed';
"""


def observation_id_for(*, source: str, source_file_ref: str,
                       source_content_sha256: str, source_row_number: int) -> str:
    """Return an internal row-observation key, never a source transaction ID."""
    source = _required_text(source, "source")
    source_file_ref = _safe_relative_ref(source_file_ref)
    source_content_sha256 = _require_sha256(source_content_sha256, "source_content_sha256")
    source_row_number = _positive_int(source_row_number, "source_row_number")
    material = "|".join(("observation-v1", source, source_file_ref,
                         source_content_sha256, str(source_row_number)))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def connect_rental(db_path: Path) -> sqlite3.Connection:
    """Open an isolated rental DB; refuse to add rental tables to another DB."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    tables = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    if tables and not tables.issubset(_RENTAL_TABLES):
        connection.close()
        raise ValueError("Refusing to mix rental tables into a non-rental database")
    try:
        connection.executescript(_SCHEMA)
        for table in sorted(_IMMUTABLE_TABLES):
            if table == "rental_snapshots":
                connection.execute(
                    "CREATE TRIGGER IF NOT EXISTS seal_rental_snapshots_once "
                    "BEFORE UPDATE ON rental_snapshots "
                    "WHEN OLD.sealed = 1 OR NEW.sealed != 1 "
                    "OR NEW.snapshot_id IS NOT OLD.snapshot_id "
                    "OR NEW.snapshot_date IS NOT OLD.snapshot_date "
                    "OR NEW.created_at_utc IS NOT OLD.created_at_utc "
                    "OR NEW.source_manifest_json IS NOT OLD.source_manifest_json "
                    "OR NEW.schema_version IS NOT OLD.schema_version "
                    "OR NEW.quality_status IS NOT OLD.quality_status "
                    "BEGIN SELECT RAISE(ABORT, 'rental snapshots are immutable'); END"
                )
                connection.execute(
                    "CREATE TRIGGER IF NOT EXISTS deny_delete_rental_snapshots "
                    "BEFORE DELETE ON rental_snapshots "
                    "BEGIN SELECT RAISE(ABORT, 'rental snapshots are immutable'); END"
                )
            else:
                for action in ("UPDATE", "DELETE"):
                    trigger = f"deny_{action.casefold()}_{table}"
                    connection.execute(
                        f"CREATE TRIGGER IF NOT EXISTS {trigger} BEFORE {action} ON {table} "
                        "BEGIN SELECT RAISE(ABORT, 'rental snapshots are immutable'); END"
                    )
                trigger = f"deny_insert_sealed_{table}"
                connection.execute(
                    f"CREATE TRIGGER IF NOT EXISTS {trigger} BEFORE INSERT ON {table} "
                    "WHEN (SELECT sealed FROM rental_snapshots WHERE snapshot_id = NEW.snapshot_id) = 1 "
                    "BEGIN SELECT RAISE(ABORT, 'rental snapshots are immutable'); END"
                )
        row = connection.execute(
            "SELECT schema_version FROM rental_schema WHERE singleton = 1").fetchone()
        if row is None:
            connection.execute("INSERT INTO rental_schema VALUES (1, ?)", (RENTAL_SCHEMA_VERSION,))
        elif row["schema_version"] != RENTAL_SCHEMA_VERSION:
            raise ValueError(f"Unsupported rental schema version: {row['schema_version']}")
        connection.commit()
    except Exception:
        connection.close()
        raise
    return connection


def import_rental_snapshot(
    connection: sqlite3.Connection, *, snapshot_id: str, snapshot_date: str,
    source_manifest: Mapping[str, object], observations: Iterable[Mapping[str, object]],
    complexes: Iterable[Mapping[str, object]] = (),
    facilities: Iterable[Mapping[str, object]] = (),
    coverage: Iterable[Mapping[str, object]] = (),
    matches: Iterable[Mapping[str, object]] = (), quality_status: str = "synthetic_only",
) -> dict[str, int]:
    """Insert one immutable snapshot with explicit lineage and reviewed joins."""
    snapshot_id = _required_text(snapshot_id, "snapshot_id")
    cutoff = _iso_date(snapshot_date, "snapshot_date")
    if quality_status not in {"synthetic_only", "source_unverified"}:
        raise ValueError("Invalid rental snapshot quality_status")
    manifest = _validate_manifest(source_manifest)
    manifest_files = _manifest_file_index(manifest)
    manifest_json = json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
    obs_rows, complex_rows = list(observations), list(complexes)
    facility_rows, coverage_rows, match_rows = list(facilities), list(coverage), list(matches)
    ingested_at = _utc_now()

    with connection:
        connection.execute(
            "INSERT INTO rental_snapshots VALUES (?, ?, ?, ?, ?, ?, 0)",
            (snapshot_id, cutoff.isoformat(), ingested_at, manifest_json,
             RENTAL_SCHEMA_VERSION, quality_status),
        )
        observation_ids: set[str] = set()
        for item in obs_rows:
            _assert_manifest_binding(item, manifest_files)
            row = _normalize_observation(item, cutoff)
            if row["observation_id"] in observation_ids:
                raise ValueError("Duplicate observation key in rental snapshot")
            observation_ids.add(row["observation_id"])
            connection.execute(
                """INSERT INTO rental_observations VALUES
                   (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (snapshot_id, row["observation_id"], row["source"], row["source_record_id"],
                 row["source_file_ref"], row["source_content_sha256"], row["source_row_number"],
                 row["sgg_cd"], row["legal_dong"], row["apartment_name"], row["jibun"],
                 row["contract_date"], row["rental_type"], row["deposit_krw"],
                 row["monthly_rent_krw"], row["area_sqm"], row["floor"], row["build_year"],
                 row["contract_term"], row["contract_type"], row["renewal_right_used"],
                 row["previous_deposit_krw"], row["previous_monthly_rent_krw"],
                 row["source_status"], ingested_at, row["raw_payload_json"]),
            )

        complex_ids: set[str] = set()
        for item in complex_rows:
            _assert_manifest_binding(item, manifest_files)
            row = _normalize_complex(item)
            if row["complex_id"] in complex_ids:
                raise ValueError("Duplicate complex_id in rental snapshot")
            complex_ids.add(row["complex_id"])
            connection.execute(
                "INSERT INTO rental_complexes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (snapshot_id, row["complex_id"], row["name"], row["sgg_cd"], row["legal_dong"],
                 row["jibun"], row["latitude"], row["longitude"], row["identity_evidence"],
                 row["source"], row["source_record_id"], row["source_file_ref"],
                 row["source_content_sha256"], row["source_row_number"], ingested_at,
                 row["raw_payload_json"]),
            )

        facility_ids: set[str] = set()
        for item in facility_rows:
            _assert_manifest_binding(item, manifest_files)
            row = _normalize_facility(item)
            if row["facility_observation_id"] in facility_ids:
                raise ValueError("Duplicate facility observation key in rental snapshot")
            facility_ids.add(row["facility_observation_id"])
            connection.execute(
                "INSERT INTO rental_facilities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (snapshot_id, row["facility_observation_id"], row["source_facility_id"],
                 row["category"], row["name"], row["sgg_cd"], row["latitude"], row["longitude"],
                 row["source"], row["source_file_ref"], row["source_content_sha256"],
                 row["source_row_number"], ingested_at, row["raw_payload_json"]),
            )

        for item in coverage_rows:
            _assert_manifest_binding(item, manifest_files)
            row = _normalize_coverage(item)
            connection.execute(
                "INSERT INTO rental_facility_coverage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (snapshot_id, row["category"], row["sgg_cd"], row["coverage_status"],
                 row["covered_feature_count"], row["source"], row["source_record_id"],
                 row["source_file_ref"], row["source_content_sha256"], row["checked_at_utc"],
                 row["raw_payload_json"]),
            )

        for item in match_rows:
            row = _normalize_match(item)
            if row["observation_id"] not in observation_ids:
                raise ValueError("Complex match references an unknown observation")
            if row["complex_id"] not in complex_ids:
                raise ValueError("Complex match references an unknown complex")
            connection.execute(
                "INSERT INTO rental_observation_matches VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (snapshot_id, row["observation_id"], row["complex_id"], row["review_status"],
                 row["match_basis"], row["evidence"], row["reviewed_by"], row["reviewed_at_utc"]),
            )
        connection.execute("UPDATE rental_snapshots SET sealed = 1 WHERE snapshot_id = ?",
                           (snapshot_id,))

    return {"observations": len(obs_rows), "complexes": len(complex_rows),
            "facilities": len(facility_rows), "coverage": len(coverage_rows),
            "matches": len(match_rows)}


def _normalize_observation(item: Mapping[str, object], cutoff: date) -> dict[str, object]:
    source, file_ref, digest, row_number = _provenance(item)
    key = observation_id_for(source=source, source_file_ref=file_ref,
                             source_content_sha256=digest, source_row_number=row_number)
    if item.get("observation_id") != key:
        raise ValueError("observation_id is not the expected internal provenance key")
    contract_date = _iso_date(item.get("contract_date"), "contract_date")
    if contract_date > cutoff:
        raise ValueError("contract_date exceeds rental snapshot_date")
    deposit = _nonnegative_int(item.get("deposit_krw"), "deposit_krw")
    monthly = _nonnegative_int(item.get("monthly_rent_krw"), "monthly_rent_krw")
    rental_type = _required_text(item.get("rental_type"), "rental_type")
    if rental_type != ("jeonse" if monthly == 0 else "wolse"):
        raise ValueError("rental_type conflicts with monthly_rent_krw")
    raw = _json_object(item.get("raw_payload", {}), "raw_payload")
    return {
        "observation_id": key, "source": source,
        "source_record_id": _optional_text(item.get("source_record_id")),
        "source_file_ref": file_ref, "source_content_sha256": digest,
        "source_row_number": row_number, "sgg_cd": _optional_region(item.get("sgg_cd")),
        "legal_dong": _optional_text(item.get("legal_dong")),
        "apartment_name": _required_text(item.get("apartment_name"), "apartment_name"),
        "jibun": _optional_text(item.get("jibun")), "contract_date": contract_date.isoformat(),
        "rental_type": rental_type, "deposit_krw": deposit, "monthly_rent_krw": monthly,
        "area_sqm": _positive_finite(item.get("area_sqm"), "area_sqm"),
        "floor": _optional_int(item.get("floor"), "floor"),
        "build_year": _optional_int(item.get("build_year"), "build_year"),
        "contract_term": _optional_text(item.get("contract_term")),
        "contract_type": _optional_text(item.get("contract_type")),
        "renewal_right_used": _optional_text(item.get("renewal_right_used")),
        "previous_deposit_krw": _optional_nonnegative_int(item.get("previous_deposit_krw"), "previous_deposit_krw"),
        "previous_monthly_rent_krw": _optional_nonnegative_int(
            item.get("previous_monthly_rent_krw"), "previous_monthly_rent_krw"),
        "source_status": _optional_text(item.get("source_status")),
        "raw_payload_json": json.dumps(raw, ensure_ascii=False, sort_keys=True,
                                        separators=(",", ":"), allow_nan=False),
    }


def _normalize_complex(item: Mapping[str, object]) -> dict[str, object]:
    source, file_ref, digest, row_number = _provenance(item)
    latitude, longitude = _coordinates(item.get("latitude"), item.get("longitude"))
    return {
        "complex_id": _required_text(item.get("complex_id"), "complex_id"),
        "name": _required_text(item.get("name"), "name"),
        "sgg_cd": _required_region(item.get("sgg_cd")),
        "legal_dong": _optional_text(item.get("legal_dong")), "jibun": _optional_text(item.get("jibun")),
        "latitude": latitude, "longitude": longitude,
        "identity_evidence": _required_text(item.get("identity_evidence"), "identity_evidence"),
        "source": source, "source_record_id": _optional_text(item.get("source_record_id")),
        "source_file_ref": file_ref, "source_content_sha256": digest,
        "source_row_number": row_number,
        "raw_payload_json": json.dumps(_json_object(item.get("raw_payload", {}), "raw_payload"),
                                        ensure_ascii=False, sort_keys=True,
                                        separators=(",", ":"), allow_nan=False),
    }


def _normalize_facility(item: Mapping[str, object]) -> dict[str, object]:
    source, file_ref, digest, row_number = _provenance(item)
    latitude, longitude = _coordinates(item.get("latitude"), item.get("longitude"), required=True)
    category = _required_text(item.get("category"), "category")
    if category not in _FACILITY_CATEGORIES:
        raise ValueError(f"Unsupported facility category: {category}")
    facility_id = observation_id_for(source=source, source_file_ref=file_ref,
                                     source_content_sha256=digest, source_row_number=row_number)
    if item.get("facility_observation_id") != facility_id:
        raise ValueError("facility_observation_id is not the expected internal provenance key")
    return {
        "facility_observation_id": facility_id,
        "source_facility_id": _optional_text(item.get("source_facility_id")),
        "category": category, "name": _required_text(item.get("name"), "name"),
        "sgg_cd": _optional_region(item.get("sgg_cd")), "latitude": latitude,
        "longitude": longitude, "source": source, "source_file_ref": file_ref,
        "source_content_sha256": digest, "source_row_number": row_number,
        "raw_payload_json": json.dumps(_json_object(item.get("raw_payload", {}), "raw_payload"),
                                        ensure_ascii=False, sort_keys=True,
                                        separators=(",", ":"), allow_nan=False),
    }


def _normalize_coverage(item: Mapping[str, object]) -> dict[str, object]:
    source, file_ref, digest, _ = _provenance(item)
    category = _required_text(item.get("category"), "category")
    if category not in _FACILITY_CATEGORIES:
        raise ValueError(f"Unsupported facility category: {category}")
    status = _required_text(item.get("coverage_status"), "coverage_status")
    if status not in {"complete", "partial", "unknown"}:
        raise ValueError("Invalid coverage_status")
    return {
        "category": category, "sgg_cd": _required_region(item.get("sgg_cd")),
        "coverage_status": status,
        "covered_feature_count": _optional_nonnegative_int(
            item.get("covered_feature_count"), "covered_feature_count"),
        "source": source, "source_record_id": _optional_text(item.get("source_record_id")),
        "source_file_ref": file_ref, "source_content_sha256": digest,
        "checked_at_utc": _utc_timestamp(item.get("checked_at_utc"), "checked_at_utc"),
        "raw_payload_json": json.dumps(_json_object(item.get("raw_payload", {}), "raw_payload"),
                                        ensure_ascii=False, sort_keys=True,
                                        separators=(",", ":"), allow_nan=False),
    }


def _normalize_match(item: Mapping[str, object]) -> dict[str, object]:
    status = _required_text(item.get("review_status"), "review_status")
    if status not in {"pending", "confirmed", "rejected"}:
        raise ValueError("Invalid complex match review_status")
    evidence = _optional_text(item.get("evidence"))
    reviewer = _optional_text(item.get("reviewed_by"))
    reviewed_at = item.get("reviewed_at_utc")
    if status == "confirmed":
        if not evidence or not reviewer:
            raise ValueError("Confirmed complex matches require evidence and reviewer")
        reviewed_at = _utc_timestamp(reviewed_at, "reviewed_at_utc")
    elif reviewed_at is not None:
        reviewed_at = _utc_timestamp(reviewed_at, "reviewed_at_utc")
    return {
        "observation_id": _required_text(item.get("observation_id"), "observation_id"),
        "complex_id": _required_text(item.get("complex_id"), "complex_id"),
        "review_status": status, "match_basis": _required_text(item.get("match_basis"), "match_basis"),
        "evidence": evidence, "reviewed_by": reviewer, "reviewed_at_utc": reviewed_at,
    }


def _validate_manifest(manifest: Mapping[str, object]) -> dict[str, object]:
    body = _json_object(manifest, "source_manifest")
    _assert_no_credentials(body)
    datasets = body.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("source_manifest.datasets must contain at least one source")
    for dataset in datasets:
        if not isinstance(dataset, dict):
            raise ValueError("Each source manifest dataset must be an object")
        _required_text(dataset.get("source"), "manifest source")
        files = dataset.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("Each source manifest dataset needs at least one file")
        for file in files:
            if not isinstance(file, dict):
                raise ValueError("Each manifest file must be an object")
            _safe_relative_ref(file.get("path"))
            _require_sha256(file.get("sha256"), "manifest file sha256")
            _nonnegative_int(file.get("rows"), "manifest file rows")
        _utc_timestamp(dataset.get("retrieved_at_utc"), "manifest retrieved_at_utc")
    return body


def _manifest_file_index(manifest: Mapping[str, object]) -> dict[tuple[str, str], tuple[str, int]]:
    result: dict[tuple[str, str], tuple[str, int]] = {}
    for dataset in manifest["datasets"]:
        source = _required_text(dataset["source"], "manifest source")
        for file in dataset["files"]:
            path = _safe_relative_ref(file["path"])
            digest = _require_sha256(file["sha256"], "manifest file sha256")
            row_count = _nonnegative_int(file["rows"], "manifest file rows")
            key = (source, path)
            if key in result:
                raise ValueError("A source file may appear only once in the manifest")
            result[key] = (digest, row_count)
    return result


def _assert_manifest_binding(item: Mapping[str, object],
                             manifest_files: Mapping[tuple[str, str], tuple[str, int]]) -> None:
    source, file_ref, digest, row_number = _provenance(item)
    file = manifest_files.get((source, file_ref))
    if file is None or file[0] != digest:
        raise ValueError("Imported row provenance does not match a source manifest file")
    if row_number > file[1]:
        raise ValueError("Imported source_row_number exceeds the manifest row count")


def _provenance(item: Mapping[str, object]) -> tuple[str, str, str, int]:
    return (_required_text(item.get("source"), "source"),
            _safe_relative_ref(item.get("source_file_ref")),
            _require_sha256(item.get("source_content_sha256"), "source_content_sha256"),
            _positive_int(item.get("source_row_number"), "source_row_number"))


def _safe_relative_ref(value: object) -> str:
    text = _required_text(value, "source_file_ref").replace("\\", "/")
    parts = text.split("/")
    if text.startswith("/") or any(part in {"", ".", ".."} for part in parts) or ":" in text:
        raise ValueError("Source file references must stay inside the rental snapshot")
    return text


def _require_sha256(value: object, field: str) -> str:
    text = _required_text(value, field)
    if not _SHA256.fullmatch(text):
        raise ValueError(f"{field} must be a lowercase SHA-256 hex digest")
    return text


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Optional source text fields must be text or null")
    return value.strip() or None


def _json_object(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    result = dict(value)
    json.dumps(result, ensure_ascii=False, allow_nan=False)
    _assert_no_credentials(result)
    return result


def _assert_no_credentials(value: object) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if normalized in _CREDENTIAL_FIELDS:
                raise ValueError("Credentials are forbidden in rental source data")
            _assert_no_credentials(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_credentials(nested)


def _iso_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} must be an ISO date") from None


def _utc_timestamp(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{field} must be an ISO-8601 timestamp with timezone") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _optional_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer or null")
    return value


def _optional_nonnegative_int(value: object, field: str) -> int | None:
    return None if value is None else _nonnegative_int(value, field)


def _positive_finite(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a positive finite number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be a positive finite number")
    return number


def _coordinates(latitude: object, longitude: object,
                 *, required: bool = False) -> tuple[float | None, float | None]:
    if latitude is None and longitude is None and not required:
        return None, None
    if isinstance(latitude, bool) or isinstance(longitude, bool) or not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        raise ValueError("Coordinates must be supplied together as WGS84 numeric values")
    lat, lon = float(latitude), float(longitude)
    if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("Coordinates fall outside the WGS84 latitude/longitude range")
    return lat, lon


def _required_region(value: object) -> str:
    text = _required_text(value, "sgg_cd")
    if not re.fullmatch(r"\d{5}", text):
        raise ValueError("sgg_cd must be a five-digit district code")
    return text


def _optional_region(value: object) -> str | None:
    return None if value is None else _required_region(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

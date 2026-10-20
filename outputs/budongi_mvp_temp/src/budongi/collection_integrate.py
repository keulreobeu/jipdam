"""Offline canonical snapshots: source facts are separate from batch membership.

Verified XML -> raw content/rows -> batch validation -> versioned observations
            -> official source entities / pending candidates -> sealed snapshot.
Previous snapshots are only read. Incremental imports publish a new snapshot.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import date
from pathlib import Path

from .collection import (CollectionError, SERVICES, digest_file, load_query, utc_now,
                         query_folder, read_json, safe_file, verify_query, write_json)
from .collection_db import normalize_row, validate_normalized_inputs
from .rental_recommendation import SEOUL_DISTRICTS
from .rental_storage import observation_id_for

SCHEMA_VERSION = "canonical_real_estate_v3"
SCHEMA = """
PRAGMA foreign_keys=ON;
PRAGMA user_version=3;
CREATE TABLE sources(source_id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL UNIQUE,
 format TEXT NOT NULL, documentation TEXT NOT NULL);
CREATE TABLE regions(sgg_cd TEXT PRIMARY KEY CHECK(length(sgg_cd)=5), name TEXT NOT NULL);
CREATE TABLE batches(batch_id TEXT PRIMARY KEY, source_batch_id TEXT NOT NULL,
 mapping_version TEXT NOT NULL, snapshot_date TEXT NOT NULL, observation_from TEXT NOT NULL,
 record_url TEXT NOT NULL, complete INTEGER NOT NULL CHECK(complete IN(0,1)),
 input_signature TEXT NOT NULL CHECK(length(input_signature)=64), archive_root TEXT NOT NULL,
 UNIQUE(source_batch_id,mapping_version));
CREATE TABLE coverage(batch_id TEXT NOT NULL REFERENCES batches, source_id TEXT NOT NULL REFERENCES sources,
 sgg_cd TEXT NOT NULL REFERENCES regions, contract_month TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('complete','complete_zero','not_collected','partial','failed')),
 expected_rows INTEGER CHECK(expected_rows>=0), received_rows INTEGER NOT NULL CHECK(received_rows>=0), error TEXT,
 PRIMARY KEY(batch_id,source_id,sgg_cd,contract_month));
CREATE TABLE raw_blobs(sha256 TEXT PRIMARY KEY CHECK(length(sha256)=64), byte_count INTEGER NOT NULL CHECK(byte_count>=0));
CREATE TABLE raw_files(file_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources,
 file_ref TEXT NOT NULL, sha256 TEXT NOT NULL REFERENCES raw_blobs, raw_rows INTEGER NOT NULL CHECK(raw_rows>=0),
 UNIQUE(source_id,file_ref,sha256));
CREATE TABLE batch_files(batch_id TEXT NOT NULL REFERENCES batches, file_id TEXT NOT NULL REFERENCES raw_files,
 sgg_cd TEXT REFERENCES regions, contract_month TEXT, retrieved_at_utc TEXT NOT NULL,
 PRIMARY KEY(batch_id,file_id));
CREATE TABLE raw_items(raw_item_id TEXT PRIMARY KEY, legacy_observation_id TEXT NOT NULL,
 file_id TEXT NOT NULL REFERENCES raw_files, section TEXT NOT NULL,
 row_number INTEGER NOT NULL CHECK(row_number>0), raw_payload_json TEXT NOT NULL CHECK(json_valid(raw_payload_json)),
 UNIQUE(file_id,section,row_number));
CREATE INDEX raw_legacy ON raw_items(legacy_observation_id);
CREATE TABLE staging_items(batch_id TEXT NOT NULL REFERENCES batches, raw_item_id TEXT NOT NULL REFERENCES raw_items,
 validation_status TEXT NOT NULL CHECK(validation_status IN('valid','outside_period','rejected')),
 rejection_reason TEXT, PRIMARY KEY(batch_id,raw_item_id),
 CHECK((validation_status='valid' AND rejection_reason IS NULL)
 OR (validation_status!='valid' AND length(trim(rejection_reason))>0)));
CREATE INDEX staging_state ON staging_items(batch_id,validation_status);
CREATE TABLE complexes(complex_id TEXT PRIMARY KEY, sgg_cd TEXT NOT NULL REFERENCES regions,
 identifier_namespace TEXT NOT NULL, source_complex_id TEXT NOT NULL, identity_basis TEXT NOT NULL,
 UNIQUE(identifier_namespace,source_complex_id));
CREATE TABLE addresses(address_id TEXT PRIMARY KEY, sgg_cd TEXT NOT NULL REFERENCES regions,
 legal_dong_code TEXT NOT NULL CHECK(length(legal_dong_code)=5),
 main_number TEXT NOT NULL CHECK(length(main_number)=4), sub_number TEXT NOT NULL CHECK(length(sub_number)=4),
 land_code TEXT NOT NULL CHECK(length(land_code)=1), identity_basis TEXT NOT NULL,
 UNIQUE(sgg_cd,legal_dong_code,main_number,sub_number,land_code));
CREATE TABLE buildings(building_id TEXT PRIMARY KEY, identifier_namespace TEXT NOT NULL,
 source_building_id TEXT NOT NULL, sgg_cd TEXT NOT NULL REFERENCES regions,
 complex_id TEXT REFERENCES complexes, address_id TEXT REFERENCES addresses, identity_basis TEXT NOT NULL,
 UNIQUE(identifier_namespace,source_building_id));
CREATE TABLE observations(observation_id TEXT PRIMARY KEY, raw_item_id TEXT NOT NULL REFERENCES raw_items,
 mapping_version TEXT NOT NULL, source_id TEXT NOT NULL REFERENCES sources,
 sgg_cd TEXT NOT NULL REFERENCES regions, complex_id TEXT REFERENCES complexes,
 building_id TEXT REFERENCES buildings, contract_date TEXT NOT NULL, apartment_name TEXT NOT NULL,
 legal_dong TEXT, jibun TEXT, kind TEXT NOT NULL CHECK(kind IN('jeonse','wolse','sale')),
 area_sqm REAL NOT NULL CHECK(area_sqm>0), deposit_krw INTEGER CHECK(deposit_krw>=0),
 monthly_rent_krw INTEGER CHECK(monthly_rent_krw>=0), price_krw INTEGER CHECK(price_krw>=0),
 source_record_id TEXT, floor INTEGER, build_year INTEGER, source_effective_from TEXT, source_effective_to TEXT,
 normalized_payload_json TEXT NOT NULL CHECK(json_valid(normalized_payload_json)),
 UNIQUE(raw_item_id,mapping_version),
 CHECK((kind IN('jeonse','wolse') AND deposit_krw IS NOT NULL AND monthly_rent_krw IS NOT NULL AND price_krw IS NULL)
 OR (kind='sale' AND price_krw IS NOT NULL AND deposit_krw IS NULL AND monthly_rent_krw IS NULL)),
 CHECK(kind!='jeonse' OR monthly_rent_krw=0), CHECK(kind!='wolse' OR monthly_rent_krw>0));
CREATE INDEX observation_labels ON observations(sgg_cd,legal_dong,jibun,apartment_name);
CREATE INDEX observation_complex ON observations(complex_id);
CREATE TABLE batch_observations(batch_id TEXT NOT NULL REFERENCES batches,
 observation_id TEXT NOT NULL REFERENCES observations, PRIMARY KEY(batch_id,observation_id));
CREATE TABLE complex_address_evidence(complex_id TEXT NOT NULL REFERENCES complexes,
 address_id TEXT NOT NULL REFERENCES addresses, observation_id TEXT NOT NULL REFERENCES observations,
 evidence TEXT NOT NULL, PRIMARY KEY(complex_id,address_id,observation_id));
CREATE TABLE identity_conflicts(batch_id TEXT NOT NULL REFERENCES batches, raw_item_id TEXT NOT NULL REFERENCES raw_items,
 identifier_namespace TEXT NOT NULL, source_identifier TEXT NOT NULL, reason TEXT NOT NULL,
 evidence_json TEXT NOT NULL CHECK(json_valid(evidence_json)), PRIMARY KEY(batch_id,raw_item_id,identifier_namespace));
CREATE TABLE match_candidates(batch_id TEXT NOT NULL REFERENCES batches,
 observation_id TEXT NOT NULL REFERENCES observations, complex_id TEXT NOT NULL REFERENCES complexes,
 supporting_observation_id TEXT NOT NULL REFERENCES observations,
 review_status TEXT NOT NULL CHECK(review_status='pending'),
 confidence TEXT NOT NULL CHECK(confidence='unverified'), confidence_score REAL CHECK(confidence_score BETWEEN 0 AND 1),
 match_basis TEXT NOT NULL, evidence TEXT NOT NULL, PRIMARY KEY(batch_id,observation_id,complex_id));
"""
KEYS = {
    "sources": ("source_id",), "regions": ("sgg_cd",), "batches": ("batch_id",),
    "coverage": ("batch_id", "source_id", "sgg_cd", "contract_month"),
    "raw_blobs": ("sha256",), "raw_files": ("file_id",), "batch_files": ("batch_id", "file_id"),
    "raw_items": ("raw_item_id",), "staging_items": ("batch_id", "raw_item_id"),
    "complexes": ("complex_id",), "addresses": ("address_id",), "buildings": ("building_id",),
    "observations": ("observation_id",), "batch_observations": ("batch_id", "observation_id"),
    "complex_address_evidence": ("complex_id", "address_id", "observation_id"),
    "identity_conflicts": ("batch_id", "raw_item_id", "identifier_namespace"),
    "match_candidates": ("batch_id", "observation_id", "complex_id"),
}


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _key(*parts) -> str:
    return hashlib.sha256(_json(parts).encode("utf-8")).hexdigest()


def _reader(path: Path):
    c = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def _put(c, table: str, values: tuple):
    """Only exact repetitions are ignored; a unique-key disagreement is an error."""
    keys = KEYS[table]
    cursor = c.execute(f"INSERT INTO {table} VALUES ({','.join('?' for _ in values)}) ON CONFLICT DO NOTHING", values)
    if cursor.rowcount:
        return
    existing = c.execute(f"SELECT * FROM {table} WHERE " + " AND ".join(k + "=?" for k in keys), values[:len(keys)]).fetchone()
    if existing is None or tuple(existing) != values:
        raise CollectionError("canonical_identity_content_conflict_" + table)


def _previous(c, directory: Path, *, quality_status="source_unverified"):
    report = read_json(directory / "quality-report.json")
    previous_version = report.get("schema_version")
    if report.get("quality_status") != quality_status:
        raise CollectionError("canonical_quality_domains_must_not_mix")
    if previous_version not in {SCHEMA_VERSION, "canonical_real_estate_v2"} or set(report.get("files", {})) != {"canonical.sqlite3"}:
        raise CollectionError("unsupported_previous_canonical_schema")
    path = safe_file(directory, "canonical.sqlite3")
    if digest_file(path) != report["files"]["canonical.sqlite3"]:
        raise CollectionError("previous_canonical_integrity_failed")
    source = _reader(path)
    try:
        expected_version = 2 if previous_version == "canonical_real_estate_v2" else 3
        if source.execute("PRAGMA user_version").fetchone()[0] != expected_version or source.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or source.execute("PRAGMA foreign_key_check").fetchall():
            raise CollectionError("previous_canonical_integrity_failed")
        source.backup(c)
    finally:
        source.close()
    # This changes only the newly created copy; the input snapshot stays sealed.
    for table in KEYS:
        for action in ("INSERT", "UPDATE", "DELETE"):
            c.execute(f"DROP TRIGGER IF EXISTS seal_{table}_{action}")
    if previous_version == "canonical_real_estate_v2":
        # Only the new copy is migrated. A multi-region/month file has no single
        # region/month; coverage and observations retain the row-level scope.
        c.executescript("""ALTER TABLE batch_files RENAME TO batch_files_v2;
            CREATE TABLE batch_files(batch_id TEXT NOT NULL REFERENCES batches,
                file_id TEXT NOT NULL REFERENCES raw_files, sgg_cd TEXT REFERENCES regions,
                contract_month TEXT, retrieved_at_utc TEXT NOT NULL, PRIMARY KEY(batch_id,file_id));
            INSERT INTO batch_files SELECT * FROM batch_files_v2;
            DROP TABLE batch_files_v2;
            PRAGMA user_version=3;""")


def _official_complex(c, batch, raw_item, row, raw):
    identifier = row.get("source_complex_id")
    if row["source"] != SERVICES["trade-detail"]["source"] or not identifier:
        return None
    namespace = "molit_apt_trade_detail:aptSeq"
    key = _key(namespace, identifier)
    old = c.execute("SELECT sgg_cd FROM complexes WHERE complex_id=?", (key,)).fetchone()
    prefix = identifier.split("-", 1)[0]
    conflict = (old and old[0] != row["sgg_cd"]) or (len(prefix) == 5 and prefix.isdigit() and prefix != row["sgg_cd"])
    if conflict:
        _put(c, "identity_conflicts", (batch, raw_item, namespace, identifier, "official_identifier_region_conflict",
             _json({"reported_region": row["sgg_cd"], "existing_region": old[0] if old else None, "identifier": identifier})))
        return None
    _put(c, "complexes", (key, row["sgg_cd"], namespace, identifier, "source aptSeq; not a transaction or building identifier"))
    return key


def _address(c, complex_id, observation_id, row, raw):
    components = [str(raw.get(k) or "").strip() for k in ("umdCd", "bonbun", "bubun", "landCd")]
    if not all(v.isascii() and v.isdigit() for v in components):
        return
    if len(components[0]) != 5 or not 1 <= len(components[1]) <= 4 or not 1 <= len(components[2]) <= 4 or len(components[3]) != 1:
        return
    components[1:3] = [v.zfill(4) for v in components[1:3]]
    address_id = _key("molit_cadastral_components", row["sgg_cd"], *components)
    _put(c, "addresses", (address_id, row["sgg_cd"], *components, "source cadastral components; no geocoding or building inference"))
    _put(c, "complex_address_evidence", (complex_id, address_id, observation_id, "MOLIT detailed XML umdCd/bonbun/bubun/landCd"))


def _raw_input(c, root, plan, status, batch):
    for q in status["queries"]:
        manifest = load_query(root, plan, q["service"], q["district"], q["month"])
        expected = manifest["pages"][0]["total"] if manifest["pages"] else None
        source = SERVICES[q["service"]]["source"]
        _put(c, "coverage", (batch, source, q["district"], q["month"], q["status"], expected, q["row_count"], q["error"]))
        if q["status"] not in {"complete", "complete_zero"}:
            continue
        folder = query_folder(root, q["service"], q["district"], q["month"])
        for page in verify_query(folder, manifest, require_complete=True):
            reference = (folder / page["file"]).relative_to(root).as_posix()
            file_id = _key(source, reference, page["sha256"])
            _put(c, "raw_blobs", (page["sha256"], (folder / page["file"]).stat().st_size))
            _put(c, "raw_files", (file_id, source, reference, page["sha256"], page["rows"]))
            _put(c, "batch_files", (batch, file_id, q["district"], q["month"], page["retrieved_at_utc"]))
            for index, raw in enumerate(page["raw_rows"], 1):
                provenance = {"source": source, "source_file_ref": reference, "source_content_sha256": page["sha256"], "source_row_number": index}
                raw_item = _key(file_id, "items", index)
                legacy = observation_id_for(**provenance)
                _put(c, "raw_items", (raw_item, legacy, file_id, "items", index, _json(raw)))
                row = normalize_row(raw, provenance, rental=q["service"] == "rental")
                # A detailed-source aptSeq identifies a source complex independently
                # of whether this transaction belongs to the canonical observation
                # window. Preserve that official entity from every retained row.
                if q["service"] == "trade-detail":
                    _official_complex(c, batch, raw_item, row, raw)
                valid = plan["observation_from"] <= row["contract_date"] <= plan["snapshot_date"]
                _put(c, "staging_items", (batch, raw_item, "valid" if valid else "outside_period",
                     None if valid else "contract_date_outside_observation_period"))


def _typed_input(c, db_directory, normalized, batch, *, replay=False):
    version = normalized["schema_version"]
    for filename, table, rental in (("rental.sqlite3", "rental_observations", True), ("sales.sqlite3", "sale_observations", False)):
        if filename not in normalized["files"]:
            continue
        source = _reader(db_directory / filename)
        try:
            for record in source.execute("SELECT * FROM " + table + " ORDER BY observation_id"):
                row = dict(record)
                file_id = _key(row["source"], row["source_file_ref"], row["source_content_sha256"])
                expected_raw_item = _key(file_id, "items", row["source_row_number"])
                found = c.execute("""SELECT r.raw_item_id,r.raw_payload_json,f.source_id,f.file_ref,f.sha256,r.row_number,
                       s.validation_status FROM raw_items r JOIN raw_files f USING(file_id)
                       JOIN staging_items s USING(raw_item_id) WHERE s.batch_id=? AND r.raw_item_id=?""",
                       (batch, expected_raw_item)).fetchone()
                if found is None or found[6] != "valid":
                    raise CollectionError("normalized_raw_lineage_mismatch")
                raw = json.loads(found[1])
                provenance = {"source": found[2], "source_file_ref": found[3], "source_content_sha256": found[4], "source_row_number": found[5]}
                mapped = normalize_row(raw, provenance, rental=rental)
                if raw != json.loads(row["raw_payload_json"]) or any(row.get(k) != value for k, value in mapped.items() if k != "raw_payload"):
                    raise CollectionError("normalized_value_mismatch")
                observation_id = _key(version, row["observation_id"])
                if replay:
                    existing = c.execute("SELECT raw_item_id,normalized_payload_json FROM observations WHERE observation_id=?", (observation_id,)).fetchone()
                    if existing is None or tuple(existing) != (found[0], _json(mapped)):
                        raise CollectionError("canonical_replay_normalized_value_mismatch")
                    continue
                complex_id = _official_complex(c, batch, found[0], row, raw)
                _put(c, "observations", (observation_id, found[0], version, row["source"], row["sgg_cd"], complex_id, None,
                     row["contract_date"], row["apartment_name"], row["legal_dong"], row["jibun"], row["rental_type"] if rental else "sale",
                     row["area_sqm"], row.get("deposit_krw"), row.get("monthly_rent_krw"), row.get("price_krw"),
                     row["source_record_id"], row["floor"], row["build_year"], None, None, _json(mapped)))
                _put(c, "batch_observations", (batch, observation_id))
                if complex_id:
                    _address(c, complex_id, observation_id, row, raw)
        finally:
            source.close()


def _candidates(c, batch):
    # Summarize entity evidence first; never join every transaction to every transaction.
    c.execute("""CREATE TEMP TABLE official_labels AS
        SELECT complex_id,sgg_cd,legal_dong,jibun,apartment_name,MIN(observation_id) AS supporting_observation_id
        FROM observations WHERE complex_id IS NOT NULL AND length(trim(legal_dong))>0 AND length(trim(jibun))>0
        GROUP BY complex_id,sgg_cd,legal_dong,jibun,apartment_name""")
    c.execute("CREATE INDEX official_label_lookup ON official_labels(sgg_cd,legal_dong,jibun,apartment_name)")
    for row in c.execute("""SELECT a.observation_id,b.complex_id,b.supporting_observation_id
        FROM batch_observations m JOIN observations a USING(observation_id)
        JOIN official_labels b ON a.sgg_cd=b.sgg_cd AND a.legal_dong=b.legal_dong
          AND a.jibun=b.jibun AND a.apartment_name=b.apartment_name
        WHERE m.batch_id=? AND a.complex_id IS NULL""", (batch,)):
        existing = c.execute("SELECT 1 FROM match_candidates WHERE batch_id=? AND observation_id=? AND complex_id=?", (batch, row[0], row[1])).fetchone()
        if not existing:
            _put(c, "match_candidates", (batch, *tuple(row), "pending", "unverified", None,
                 "exact district/dong/jibun/name labels; not authoritative identity", "Supporting source observation; review required"))
    c.execute("DROP TABLE official_labels")


def _audit(c, batch, normalized):
    stage_counts = dict(c.execute("SELECT validation_status,COUNT(*) FROM staging_items WHERE batch_id=? GROUP BY validation_status", (batch,)))
    raw = c.execute("SELECT COALESCE(SUM(f.raw_rows),0) FROM batch_files b JOIN raw_files f USING(file_id) WHERE b.batch_id=?", (batch,)).fetchone()[0]
    valid = c.execute("SELECT COUNT(*) FROM batch_observations WHERE batch_id=?", (batch,)).fetchone()[0]
    expected_raw = sum(v["raw_rows"] for v in normalized["counts"].values())
    expected_valid = sum(v["imported"] for v in normalized["counts"].values())
    if raw != expected_raw or raw != sum(stage_counts.values()) or valid != expected_valid or valid != stage_counts.get("valid", 0):
        raise CollectionError("canonical_count_reconciliation_failed")
    joins = c.execute("""SELECT COUNT(*) FROM batch_observations b JOIN observations o USING(observation_id)
        JOIN sources USING(source_id) JOIN regions USING(sgg_cd) JOIN raw_items r USING(raw_item_id)
        JOIN raw_files f USING(file_id) JOIN batch_files m ON m.batch_id=b.batch_id AND m.file_id=f.file_id
        JOIN staging_items t ON t.batch_id=b.batch_id AND t.raw_item_id=r.raw_item_id
        WHERE b.batch_id=? AND t.validation_status='valid'""", (batch,)).fetchone()[0]
    if joins != valid:
        raise CollectionError("canonical_lineage_join_failed")
    if c.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or c.execute("PRAGMA foreign_key_check").fetchall():
        raise CollectionError("canonical_integrity_failed")
    counts = {table: c.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] for table in KEYS}
    return {"counts": counts, "stage_counts": stage_counts,
            "batch_counts": {"raw_rows": raw, "valid": valid}, "lineage_join": joins,
            "integrity_check": "ok", "foreign_key_violations": 0,
            "official_complex_join": c.execute("SELECT COUNT(*) FROM batch_observations b JOIN observations o USING(observation_id) WHERE b.batch_id=? AND o.complex_id IS NOT NULL", (batch,)).fetchone()[0]}


def integrate_collection(root: Path, db_directory: Path, output: Path, *, previous: Path | None = None, allow_partial=False) -> dict:
    plan, status, normalized = validate_normalized_inputs(root, db_directory, allow_partial=allow_partial)
    if output.exists():
        raise CollectionError("output_exists_use_new_directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".canonical-build-", dir=output.parent))
    c = sqlite3.connect(temporary / "canonical.sqlite3")
    c.execute("PRAGMA foreign_keys=ON")
    try:
        if previous is None:
            c.executescript(SCHEMA)
        else:
            _previous(c, previous)
        baseline = {t: c.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] for t in KEYS}
        version = normalized["schema_version"]
        batch = _key(plan["batch_id"], version)
        signature = _key(normalized["plan_sha256"], normalized["raw_input_hashes"], version, normalized["complete"], normalized["counts"])
        old = c.execute("SELECT input_signature FROM batches WHERE batch_id=?", (batch,)).fetchone()
        if old and old[0] != signature:
            raise CollectionError("same_batch_different_input_requires_new_batch")
        with c:
            for service in plan["services"]:
                s = SERVICES[service]
                _put(c, "sources", (s["source"], s["dataset"], "xml", "https://www.data.go.kr/data/" + s["dataset"] + "/openapi.do"))
            for name, code in SEOUL_DISTRICTS.items():
                _put(c, "regions", (code, name))
            if not old:
                _put(c, "batches", (batch, plan["batch_id"], version, plan["snapshot_date"], plan["observation_from"],
                     plan["record_url"], int(status["complete"]), signature, str(root.resolve())))
            _raw_input(c, root, plan, status, batch)
            _typed_input(c, db_directory, normalized, batch, replay=bool(old))
            if not old:
                _candidates(c, batch)
            audit = _audit(c, batch, normalized)
        for table in KEYS:
            for action in ("INSERT", "UPDATE", "DELETE"):
                c.execute(f"CREATE TRIGGER seal_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'immutable canonical snapshot'); END")
        c.commit()
        c.close()
        c = None
        report = {"schema_version": SCHEMA_VERSION, "batch_id": batch, "source_batch_id": plan["batch_id"],
                  "mapping_version": version, "complete": status["complete"], "input_signature": signature,
                  "loaded_at_utc": utc_now(),
                  "normalized_input_hashes": normalized["files"], "reused_batch": bool(old),
                  "new_counts": {t: audit["counts"][t] - baseline[t] for t in KEYS},
                  "quality_status": "source_unverified", "matching_status": "official_id_links_and_unreviewed_candidates",
                  "unavailable_entity_fields": {"buildings": "No authoritative building identifier in registered MOLIT mapping",
                                                "coordinates": "Not collected or inferred", "source_effective_dates": "Not provided; NULL"},
                  **audit, "files": {"canonical.sqlite3": digest_file(temporary / "canonical.sqlite3")}}
        write_json(temporary / "quality-report.json", report)
        if output.exists():
            raise CollectionError("output_exists_use_new_directory")
        os.rename(temporary, output)
        return report | {"output_directory": str(output)}
    finally:
        if c is not None:
            c.close()
        if temporary.exists():
            if not temporary.resolve().is_relative_to(output.parent.resolve()) or not temporary.name.startswith(".canonical-build-"):
                raise CollectionError("unsafe_temporary_cleanup")
            shutil.rmtree(temporary)


def _file_entity(c, batch, raw_item, row, source, entity):
    identifier = row.get("source_" + entity + "_id")
    if identifier is None:
        return None
    contract = source.get("official_identifiers", {}).get(entity, {})
    namespace, basis = contract.get("namespace"), contract.get("basis")
    if not isinstance(identifier, str) or not identifier.strip() or not namespace or not basis:
        raise CollectionError("file_identifier_requires_explicit_official_contract")
    key = _key(namespace, identifier)
    table = "complexes" if entity == "complex" else "buildings"
    old = c.execute("SELECT sgg_cd FROM " + table + " WHERE " + entity + "_id=?", (key,)).fetchone()
    if old and old[0] != row["sgg_cd"]:
        _put(c, "identity_conflicts", (batch, raw_item, namespace, identifier, "official_identifier_region_conflict",
                                     _json({"reported_region": row["sgg_cd"], "existing_region": old[0]})))
        return None
    if entity == "complex":
        _put(c, table, (key, row["sgg_cd"], namespace, identifier, basis))
    else:
        # Parent relationships require a separately registered authoritative
        # association. A building ID alone is no proof of its apartment complex.
        _put(c, table, (key, namespace, identifier, row["sgg_cd"], None, None, basis))
    return key


def integrate_file(directory: Path, registry_path: Path, output: Path, *, batch_id: str,
                   snapshot_date: str, observation_from: str, record_url: str,
                   previous: Path | None = None) -> dict:
    """Publish a registered file through the same sealed canonical schema offline."""
    from .source_files import validate_staged_file, normalize_file_record
    source, manifest = validate_staged_file(directory, registry_path)
    if not batch_id.strip() or not record_url.strip():
        raise CollectionError("file_batch_and_record_required")
    if (date.fromisoformat(observation_from).isoformat() != observation_from
            or date.fromisoformat(snapshot_date).isoformat() != snapshot_date):
        raise CollectionError("file_batch_dates_require_iso_format")
    if date.fromisoformat(observation_from) > date.fromisoformat(snapshot_date):
        raise CollectionError("invalid_file_observation_period")
    if output.exists():
        raise CollectionError("output_exists_use_new_directory")
    quality = "synthetic" if source.get("fictional") else "source_unverified"
    regions = source.get("regions", {code: name for name, code in SEOUL_DISTRICTS.items()})
    if (not isinstance(regions, dict) or not regions
            or any(not isinstance(k, str) or len(k) != 5 or not k.isascii() or not k.isdigit()
                   or not isinstance(v, str) or not v.strip() for k, v in regions.items())):
        raise CollectionError("invalid_registered_regions")
    if not source.get("dataset_id") or not source.get("documentation"):
        raise CollectionError("file_source_dataset_and_documentation_required")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".canonical-build-", dir=output.parent))
    c = sqlite3.connect(temporary / "canonical.sqlite3")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    staged = None
    try:
        staged = _reader(directory / "staging.sqlite3")
        if previous is None:
            c.executescript(SCHEMA)
        else:
            _previous(c, previous, quality_status=quality)
        baseline = {t: c.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] for t in KEYS}
        version = source["mapping_version"]
        batch = _key(batch_id, version)
        signature = _key(manifest["raw_sha256"], manifest["staging_sha256"], manifest["source_contract_sha256"],
                         snapshot_date, observation_from, record_url)
        old = c.execute("SELECT input_signature FROM batches WHERE batch_id=?", (batch,)).fetchone()
        if old and old[0] != signature:
            raise CollectionError("same_batch_different_input_requires_new_batch")
        file_id = _key(source["source_id"], manifest["raw_file"], manifest["raw_sha256"])
        retrieved = staged.execute("SELECT retrieved_at_utc FROM raw_files").fetchone()[0]
        scope = {}
        valid_count = 0
        with c:
            _put(c, "sources", (source["source_id"], source["dataset_id"], source["format"], source["documentation"]))
            for code, name in regions.items():
                _put(c, "regions", (code, name))
            if not old:
                _put(c, "batches", (batch, batch_id, version, snapshot_date, observation_from, record_url, 1,
                                    signature, str(directory.resolve())))
            _put(c, "raw_blobs", (manifest["raw_sha256"], safe_file(directory, manifest["raw_file"]).stat().st_size))
            _put(c, "raw_files", (file_id, source["source_id"], manifest["raw_file"], manifest["raw_sha256"], manifest["received_rows"]))
            # NULL file-level scope is explicit; region/month belongs to rows.
            _put(c, "batch_files", (batch, file_id, None, None, retrieved))
            for record in staged.execute("SELECT * FROM staging_items ORDER BY section,row_position"):
                raw_item = _key(file_id, record["section"], record["row_position"])
                _put(c, "raw_items", (raw_item, record["observation_id"], file_id, record["section"], record["row_position"],
                                      _json(json.loads(record["raw_json"]))))
                row = normalize_file_record(json.loads(record["standard_json"]), source)
                scope_key = (row["sgg_cd"], row["contract_date"][:7].replace("-", ""))
                scope[scope_key] = scope.get(scope_key, 0) + 1
                valid = observation_from <= row["contract_date"] <= snapshot_date
                _put(c, "staging_items", (batch, raw_item, "valid" if valid else "outside_period",
                                          None if valid else "contract_date_outside_observation_period"))
                if not valid:
                    continue
                valid_count += 1
                observation = _key(version, record["observation_id"])
                payload = _json({"fields": row, "source_contract_sha256": manifest["source_contract_sha256"], "quality_status": quality})
                if old:
                    existing = c.execute("SELECT raw_item_id,normalized_payload_json FROM observations WHERE observation_id=?", (observation,)).fetchone()
                    if existing is None or tuple(existing) != (raw_item, payload):
                        raise CollectionError("canonical_replay_normalized_value_mismatch")
                    continue
                complex_id = _file_entity(c, batch, raw_item, row, source, "complex")
                building_id = _file_entity(c, batch, raw_item, row, source, "building")
                _put(c, "observations", (observation, raw_item, version, source["source_id"], row["sgg_cd"], complex_id, building_id,
                    row["contract_date"], row["apartment_name"], row.get("legal_dong"), row.get("jibun"), row["kind"],
                    row["area_sqm"], row.get("deposit_krw"), row.get("monthly_rent_krw"), row.get("price_krw"),
                    row.get("source_record_id"), row.get("floor"), row.get("build_year"),
                    row.get("source_effective_from"), row.get("source_effective_to"),
                    payload))
                _put(c, "batch_observations", (batch, observation))
                if complex_id and row.get("legal_dong_code") is not None:
                    components = [row[field] for field in ("legal_dong_code", "main_number", "sub_number", "land_code")]
                    address = _key("molit_cadastral_components", row["sgg_cd"], *components)
                    _put(c, "addresses", (address, row["sgg_cd"], *components,
                        "source cadastral components; no geocoding or building inference"))
                    _put(c, "complex_address_evidence", (complex_id, address, observation,
                                                        source["address_basis"]))
            for (region, month), count in sorted(scope.items()):
                _put(c, "coverage", (batch, source["source_id"], region, month, "complete", None, count,
                                    None))
            if not old:
                _candidates(c, batch)
            normalized = {"counts": {source["source_id"]: {"raw_rows": manifest["received_rows"], "imported": valid_count}}}
            audit = _audit(c, batch, normalized)
        for table in KEYS:
            for action in ("INSERT", "UPDATE", "DELETE"):
                c.execute(f"CREATE TRIGGER seal_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'immutable canonical snapshot'); END")
        c.commit()
        c.close()
        c = None
        if (digest_file(safe_file(directory, manifest["raw_file"])) != manifest["raw_sha256"]
                or digest_file(directory / "staging.sqlite3") != manifest["staging_sha256"]):
            raise CollectionError("file_stage_changed_during_integration")
        report = {"schema_version": SCHEMA_VERSION, "batch_id": batch, "source_batch_id": batch_id,
                  "mapping_version": version, "loaded_at_utc": utc_now(), "complete": True, "input_signature": signature,
                  "reused_batch": bool(old), "quality_status": quality, "source_descriptor": source,
                  "file_input_manifest_sha256": digest_file(directory / "manifest.json"),
                  "normalized_input_hashes": {"staging.sqlite3": manifest["staging_sha256"]},
                  "new_counts": {t: audit["counts"][t] - baseline[t] for t in KEYS},
                  "empty_sections": [s for s, n in manifest["sections"].items() if n == 0],
                  "coverage_policy": "file expected rows and all declared sections verified; row region/month groups have no independent provider total",
                  "matching_status": "official_id_links_and_unreviewed_candidates", **audit,
                  "files": {"canonical.sqlite3": digest_file(temporary / "canonical.sqlite3")}}
        write_json(temporary / "quality-report.json", report)
        if output.exists():
            raise CollectionError("output_exists_use_new_directory")
        os.rename(temporary, output)
        return report | {"output_directory": str(output)}
    finally:
        if staged is not None:
            staged.close()
        if c is not None:
            c.close()
        if temporary.exists():
            if not temporary.resolve().is_relative_to(output.parent.resolve()) or not temporary.name.startswith(".canonical-build-"):
                raise CollectionError("unsafe_temporary_cleanup")
            shutil.rmtree(temporary)

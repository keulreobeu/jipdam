"""Offline source mapping, separate observation DBs, and portable archives."""
from __future__ import annotations

import json
import math
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .collection import (CollectionError, SERVICES, collection_status, digest_file, load_plan, publish_snapshot_directory,
                         load_query, queries, query_folder, read_json, safe_file, verify_query, write_json)
from .rental_storage import connect_rental, import_rental_snapshot, observation_id_for

NORMALIZATION_VERSION = "molit_normalization_v1"
STAGING_VERSION = "molit_staging_v1"
STAGING_SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE raw_files (
 file_ref TEXT PRIMARY KEY, source TEXT NOT NULL, sha256 TEXT NOT NULL CHECK(length(sha256)=64),
 retrieved_at_utc TEXT NOT NULL, raw_rows INTEGER NOT NULL CHECK(raw_rows>=0));
CREATE TABLE staging_items (
 observation_id TEXT PRIMARY KEY, source_file_ref TEXT NOT NULL REFERENCES raw_files(file_ref),
 source_row_number INTEGER NOT NULL CHECK(source_row_number>0), raw_payload_json TEXT NOT NULL,
 validation_status TEXT NOT NULL CHECK(validation_status IN('valid','outside_period','rejected')),
 reason TEXT, normalized_payload_json TEXT,
 UNIQUE(source_file_ref,source_row_number),
 CHECK((validation_status='valid' AND reason IS NULL AND normalized_payload_json IS NOT NULL)
 OR (validation_status IN('outside_period','rejected') AND reason IS NOT NULL)));
CREATE INDEX staging_status ON staging_items(validation_status);
"""
SALE_SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE sale_snapshots (
 snapshot_id TEXT PRIMARY KEY, snapshot_date TEXT NOT NULL, normalization_version TEXT NOT NULL,
 source_manifest_json TEXT NOT NULL, quality_status TEXT NOT NULL CHECK(quality_status='source_unverified'),
 sealed INTEGER NOT NULL CHECK(sealed IN(0,1)));
CREATE TABLE sale_observations (
 snapshot_id TEXT NOT NULL REFERENCES sale_snapshots(snapshot_id), observation_id TEXT NOT NULL,
 source TEXT NOT NULL, source_record_id TEXT, source_complex_id TEXT,
 source_file_ref TEXT NOT NULL, source_content_sha256 TEXT NOT NULL, source_row_number INTEGER NOT NULL CHECK(source_row_number>0),
 sgg_cd TEXT NOT NULL, legal_dong TEXT, apartment_name TEXT NOT NULL, jibun TEXT,
 contract_date TEXT NOT NULL, price_krw INTEGER NOT NULL CHECK(price_krw>=0), area_sqm REAL NOT NULL CHECK(area_sqm>0),
 floor INTEGER, build_year INTEGER, source_status TEXT, cancellation_date TEXT,
 ingested_at_utc TEXT NOT NULL, raw_payload_json TEXT NOT NULL,
 PRIMARY KEY(snapshot_id,observation_id));
CREATE INDEX sale_region_date ON sale_observations(sgg_cd,contract_date);
CREATE INDEX sale_official_complex ON sale_observations(source_complex_id);
CREATE TRIGGER sale_no_update BEFORE UPDATE ON sale_observations BEGIN SELECT RAISE(ABORT,'immutable observations'); END;
CREATE TRIGGER sale_no_delete BEFORE DELETE ON sale_observations BEGIN SELECT RAISE(ABORT,'immutable observations'); END;
CREATE TRIGGER sale_no_append BEFORE INSERT ON sale_observations
 WHEN (SELECT sealed FROM sale_snapshots WHERE snapshot_id=NEW.snapshot_id)=1
 BEGIN SELECT RAISE(ABORT,'sealed snapshot'); END;
CREATE TRIGGER sale_snapshot_no_update BEFORE UPDATE ON sale_snapshots WHEN OLD.sealed=1
 BEGIN SELECT RAISE(ABORT,'sealed snapshot'); END;
CREATE TRIGGER sale_snapshot_no_delete BEFORE DELETE ON sale_snapshots BEGIN SELECT RAISE(ABORT,'immutable snapshot'); END;
"""


def _required(raw: dict, field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CollectionError("missing_field_" + field)
    return value.strip()


def _optional(raw: dict, field: str):
    value = raw.get(field)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _integer(raw: dict, field: str, *, optional=False):
    value = _optional(raw, field) if optional else _required(raw, field)
    if value is None:
        return None
    try:
        number = Decimal(value.replace(",", ""))
        if not number.is_finite() or number != number.to_integral_value():
            raise InvalidOperation
        result = int(number)
        if not -(2 ** 63) <= result < 2 ** 63:
            raise InvalidOperation
        return result
    except (InvalidOperation, ValueError, OverflowError):
        raise CollectionError("invalid_integer_" + field) from None


def _money(raw: dict, field: str) -> int:
    try:
        value = Decimal(_required(raw, field).replace(",", "")) * 10000
        if not value.is_finite() or value < 0 or value != value.to_integral_value() or value >= 2 ** 63:
            raise InvalidOperation
        return int(value)
    except (InvalidOperation, ValueError, OverflowError):
        raise CollectionError("invalid_money_" + field) from None


def normalize_row(raw: dict, provenance: dict, *, rental: bool) -> dict:
    try:
        contract = date(_integer(raw, "dealYear"), _integer(raw, "dealMonth"), _integer(raw, "dealDay"))
    except (ValueError, TypeError):
        raise CollectionError("invalid_contract_date") from None
    try:
        area = float(Decimal(_required(raw, "excluUseAr")))
        if not math.isfinite(area) or area <= 0:
            raise ValueError
    except (ValueError, InvalidOperation, OverflowError):
        raise CollectionError("invalid_area") from None
    record = provenance | {
        "observation_id": observation_id_for(**provenance), "source_record_id": None,
        "sgg_cd": _required(raw, "sggCd"), "legal_dong": _optional(raw, "umdNm"),
        "apartment_name": _required(raw, "aptNm"), "jibun": _optional(raw, "jibun"),
        "contract_date": contract.isoformat(), "area_sqm": area, "floor": _integer(raw, "floor", optional=True),
        "build_year": _integer(raw, "buildYear", optional=True), "raw_payload": dict(raw),
    }
    if rental:
        deposit, monthly = _money(raw, "deposit"), _money(raw, "monthlyRent")
        record.update(deposit_krw=deposit, monthly_rent_krw=monthly,
                      rental_type="jeonse" if monthly == 0 else "wolse", source_status=None,
                      contract_term=_optional(raw, "contractTerm"), contract_type=_optional(raw, "contractType"),
                      renewal_right_used=_optional(raw, "useRRRight"), previous_deposit_krw=None,
                      previous_monthly_rent_krw=None)
    else:
        record.update(price_krw=_money(raw, "dealAmount"), source_complex_id=_optional(raw, "aptSeq"),
                      source_status=_optional(raw, "cdealType"), cancellation_date=_optional(raw, "cdealDay"))
    return record


def _query_input(root: Path, plan: dict, query: tuple, staging, errors):
    service, code, month = query
    manifest = load_query(root, plan, *query)
    folder = query_folder(root, *query)
    pages = verify_query(folder, manifest, require_complete=True)
    files, records, excluded = [], [], 0
    for page in pages:
        reference = (folder / page["file"]).relative_to(root).as_posix()
        files.append({"path": reference, "sha256": page["sha256"], "rows": page["rows"]})
        staging.execute("INSERT INTO raw_files VALUES (?,?,?,?,?)", (
            reference, SERVICES[service]["source"], page["sha256"], page["retrieved_at_utc"], page["rows"]))
        for index, raw in enumerate(page["raw_rows"], 1):
            provenance = {"source": SERVICES[service]["source"], "source_file_ref": reference,
                          "source_content_sha256": page["sha256"], "source_row_number": index}
            state, reason, row = "valid", None, None
            try:
                row = normalize_row(raw, provenance, rental=service == "rental")
            except CollectionError as exc:
                state, reason = "rejected", str(exc)
                errors.append({"service": service, "district": code, "month": month,
                               **provenance, "reason": reason})
            if row is not None and not plan["observation_from"] <= row["contract_date"] <= plan["snapshot_date"]:
                state, reason = "outside_period", "contract_date_outside_observation_period"
                excluded += 1
            staging.execute("INSERT INTO staging_items VALUES (?,?,?,?,?,?,?)", (
                observation_id_for(**provenance), reference, index,
                json.dumps(raw, ensure_ascii=False, sort_keys=True), state, reason,
                json.dumps(row, ensure_ascii=False, sort_keys=True) if row is not None else None))
            if state == "valid":
                records.append(row)
    source_manifest = {"datasets": [{"source": SERVICES[service]["source"],
                       "retrieved_at_utc": pages[0]["retrieved_at_utc"], "files": files}],
                       "normalization_version": NORMALIZATION_VERSION,
                       "observation_period": [plan["observation_from"], plan["snapshot_date"]]}
    return records, source_manifest, excluded


def build_databases(root: Path, output: Path, *, allow_partial: bool = False) -> dict:
    plan = load_plan(root)
    status = collection_status(root)
    if any(q["status"] == "invalid" for q in status["queries"]):
        raise CollectionError("archive_integrity_failed")
    if not status["complete"] and not allow_partial:
        raise CollectionError("incomplete_collection")
    if output.exists():
        raise CollectionError("output_exists_use_new_directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".molit-build-", dir=output.parent))
    rental = sale = staging = None
    errors, query_reports = [], []
    counts = {s: {"raw_rows": 0, "imported": 0, "excluded_outside_period": 0, "rejected": 0}
              for s in plan["services"]}
    try:
        staging = sqlite3.connect(temporary / "staging.sqlite3")
        staging.executescript(STAGING_SCHEMA)
        if "rental" in plan["services"]:
            rental = connect_rental(temporary / "rental.sqlite3")
        if any(s != "rental" for s in plan["services"]):
            sale = sqlite3.connect(temporary / "sales.sqlite3")
            sale.executescript(SALE_SCHEMA)
        for state in status["queries"]:
            if state["status"] not in {"complete", "complete_zero"}:
                continue
            service = state["service"]
            query = (service, state["district"], state["month"])
            error_start = len(errors)
            rows, manifest, excluded = _query_input(root, plan, query, staging, errors)
            rejected = len(errors) - error_start
            raw_count = sum(f["rows"] for f in manifest["datasets"][0]["files"])
            if raw_count != len(rows) + excluded + rejected:
                raise CollectionError("normalization_count_mismatch")
            query_reports.append({"service": service, "district": state["district"], "month": state["month"],
                                  "raw_rows": raw_count, "imported": len(rows),
                                  "excluded_outside_period": excluded, "rejected": rejected})
            snapshot = f"{plan['batch_id']}_{service}_{state['district']}_{state['month']}_{NORMALIZATION_VERSION}"
            if service == "rental":
                import_rental_snapshot(rental, snapshot_id=snapshot, snapshot_date=plan["snapshot_date"],
                                       source_manifest=manifest, observations=rows, quality_status="source_unverified")
            else:
                with sale:
                    sale.execute("INSERT INTO sale_snapshots VALUES (?,?,?,?,?,0)",
                                 (snapshot, plan["snapshot_date"], NORMALIZATION_VERSION,
                                  json.dumps(manifest, ensure_ascii=False, sort_keys=True), "source_unverified"))
                    for row in rows:
                        sale.execute("INSERT INTO sale_observations VALUES (" + ",".join("?" * 21) + ")",
                                     (snapshot, row["observation_id"], row["source"], None, row["source_complex_id"],
                                      row["source_file_ref"], row["source_content_sha256"], row["source_row_number"],
                                      row["sgg_cd"], row["legal_dong"], row["apartment_name"], row["jibun"],
                                      row["contract_date"], row["price_krw"], row["area_sqm"], row["floor"],
                                      row["build_year"], row["source_status"], row["cancellation_date"],
                                      manifest["datasets"][0]["retrieved_at_utc"],
                                      json.dumps(row["raw_payload"], ensure_ascii=False, sort_keys=True)))
                    sale.execute("UPDATE sale_snapshots SET sealed=1 WHERE snapshot_id=?", (snapshot,))
            counts[service]["imported"] += len(rows)
            counts[service]["excluded_outside_period"] += excluded
            counts[service]["raw_rows"] += raw_count
            counts[service]["rejected"] += rejected
        if errors:
            # Preserve every discovered row failure even though no derived DB is published.
            write_json(root / "normalization-errors.json", {**errors[0],
                       "normalization_version": NORMALIZATION_VERSION, "errors": errors,
                       "counts": counts, "queries": query_reports})
            raise CollectionError("normalization_rejected_rows")
        raw_total = staging.execute("SELECT COALESCE(SUM(raw_rows),0) FROM raw_files").fetchone()[0]
        stage_total = staging.execute("SELECT COUNT(*) FROM staging_items").fetchone()[0]
        valid_total = staging.execute("SELECT COUNT(*) FROM staging_items WHERE validation_status='valid'").fetchone()[0]
        if raw_total != stage_total or valid_total != sum(v["imported"] for v in counts.values()):
            raise CollectionError("staging_count_mismatch")
        lineage_joins = {}
        for filename, table, connection in (("rental.sqlite3", "rental_observations", rental),
                                            ("sales.sqlite3", "sale_observations", sale)):
            if connection is None:
                continue
            # Snapshot+observation PKs cannot efficiently serve an observation-only lineage join.
            connection.execute(f"CREATE INDEX collection_lineage_id ON {table}(observation_id)")
            connection.commit()
            staging.execute("ATTACH DATABASE ? AS normalized", (str(temporary / filename),))
            actual = staging.execute(f"SELECT COUNT(*) FROM normalized.{table}").fetchone()[0]
            joined = staging.execute(f"""SELECT COUNT(*) FROM normalized.{table} o
                JOIN staging_items s USING(observation_id) JOIN raw_files f ON f.file_ref=s.source_file_ref
                WHERE s.validation_status='valid' AND o.source=f.source AND o.source_file_ref=f.file_ref
                  AND o.source_content_sha256=f.sha256 AND o.source_row_number=s.source_row_number
                  AND json(o.raw_payload_json)=json(s.raw_payload_json)""").fetchone()[0]
            if actual != joined:
                raise CollectionError("normalized_lineage_join_failed")
            lineage_joins[table] = joined
            staging.commit()
            staging.execute("DETACH DATABASE normalized")
        raw_inputs = {row[0]: row[1] for row in staging.execute("SELECT file_ref,sha256 FROM raw_files")}
        for table in ("raw_files", "staging_items"):
            for action in ("INSERT", "UPDATE", "DELETE"):
                staging.execute(f"CREATE TRIGGER seal_{table}_{action} BEFORE {action} ON {table} "
                                "BEGIN SELECT RAISE(ABORT,'immutable staging snapshot'); END")
        staging.commit()
        for connection in (rental, sale, staging):
            if connection is not None:
                if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or connection.execute("PRAGMA foreign_key_check").fetchall():
                    raise CollectionError("database_integrity_failed")
                connection.close()
        rental = sale = staging = None
        result = {"schema_version": NORMALIZATION_VERSION, "batch_id": plan["batch_id"],
                  "staging_schema_version": STAGING_VERSION,
                  "quality_status": "source_unverified", "complete": status["complete"],
                  "counts": counts, "queries": query_reports, "lineage_joins": lineage_joins,
                  "plan_sha256": digest_file(root / "plan.json"), "raw_input_hashes": raw_inputs,
                  "integrity_check": "ok", "foreign_key_violations": 0,
                  "missing_queries": [q for q in status["queries"] if q["status"] not in {"complete", "complete_zero"}],
                  "files": {p.name: digest_file(p) for p in temporary.glob("*.sqlite3")}}
        write_json(temporary / "normalized-manifest.json", result)
        if output.exists():
            raise CollectionError("output_exists_use_new_directory")
        publish_snapshot_directory(temporary, output)
        return result | {"output_directory": str(output)}
    finally:
        for connection in (rental, sale, staging):
            if connection is not None:
                connection.close()
        if temporary.exists():
            shutil.rmtree(temporary)


def summary_text(root: Path) -> str:
    plan = load_plan(root)
    status = collection_status(root)
    lines = [f"# 수집 배치 {plan['batch_id']}", "", f"- 기록: {plan['record_url'] or '미등록'}",
             f"- 관측 기간: {plan['observation_from']}~{plan['snapshot_date']}",
             f"- 조회 범위: {','.join(plan['districts'])} / {','.join(plan['months'])}",
             f"- 요청 완료: {status['completed_queries']}/{status['query_count']}",
             "- 품질: 실제 조회 시점 원본, source_unverified; 매칭·시설·추천 미검수",
             "- 방법: 지역×계약월×페이지 XML; 금액 만원→원; 원본 SHA-256 보존",
             "- 매매 일반·상세 건수는 별도 관측이며 합산한 실제 계약 수가 아님", "",
             "| 서비스 | 완료 | 성공 0건 | 실패/누락 | 관측 행 |", "| --- | --- | --- | --- | --- |"]
    for service in plan["services"]:
        states = [q for q in status["queries"] if q["service"] == service]
        done = sum(q["status"] in {"complete", "complete_zero"} for q in states)
        zero = sum(q["status"] == "complete_zero" for q in states)
        lines.append(f"| {service} | {done} | {zero} | {len(states)-done} | {status['counts_by_service'][service]} |")
    missing = [q for q in status["queries"] if q["status"] not in {"complete", "complete_zero"}]
    if missing:
        lines += ["", "누락 상세는 collection-status.json의 서비스·구·월·상태를 참고한다."]
    return "\n".join(lines) + "\n"


def validate_normalized_inputs(root: Path, db_directory: Path, *, allow_partial=False) -> tuple[dict, dict, dict]:
    """Bind derived databases to the current archive, for pack and integration."""
    plan = load_plan(root)
    status = collection_status(root)
    if any(q["status"] == "invalid" for q in status["queries"]):
        raise CollectionError("archive_integrity_failed")
    if not status["complete"] and not allow_partial:
        raise CollectionError("incomplete_collection")
    normalized = read_json(db_directory / "normalized-manifest.json")
    if (not isinstance(normalized, dict) or normalized.get("batch_id") != plan["batch_id"]
            or normalized.get("schema_version") != NORMALIZATION_VERSION):
        raise CollectionError("database_manifest_mismatch")
    current_inputs = {}
    for state in status["queries"]:
        if state["status"] not in {"complete", "complete_zero"}:
            continue
        query = (state["service"], state["district"], state["month"])
        folder = query_folder(root, *query)
        for page in verify_query(folder, load_query(root, plan, *query), require_complete=True):
            current_inputs[(folder / page["file"]).relative_to(root).as_posix()] = page["sha256"]
    if (normalized.get("plan_sha256") != digest_file(root / "plan.json")
            or normalized.get("raw_input_hashes") != current_inputs
            or normalized.get("complete") != status["complete"]):
        raise CollectionError("stale_database_rebuild_from_current_archive")
    files = normalized.get("files")
    expected_files = {"staging.sqlite3"}
    if "rental" in plan["services"]:
        expected_files.add("rental.sqlite3")
    if any(service != "rental" for service in plan["services"]):
        expected_files.add("sales.sqlite3")
    if not isinstance(files, dict) or set(files) != expected_files:
        raise CollectionError("database_manifest_mismatch")
    for name, digest in files.items():
        if digest_file(safe_file(db_directory, name)) != digest:
            raise CollectionError("database_integrity_failed")
    return plan, status, normalized


def pack_collection(root: Path, output: Path, *, db_directory: Path, allow_partial=False) -> dict:
    plan = load_plan(root)
    if not plan["record_url"]:
        raise CollectionError("github_collection_record_required")
    if output.exists():
        raise CollectionError("output_exists")
    plan, status, normalized = validate_normalized_inputs(root, db_directory, allow_partial=allow_partial)
    entries = [(root / "plan.json", "plan.json")]
    for query in queries(plan):
        folder = query_folder(root, *query)
        manifest = load_query(root, plan, *query)
        if manifest["status"] == "not_collected":
            continue
        entries.append((folder / "manifest.json", (folder / "manifest.json").relative_to(root).as_posix()))
        for attempt in manifest["attempts"]:
            if "file" not in attempt:
                continue
            path = safe_file(folder, attempt["file"])
            if not path.is_file() or digest_file(path) != attempt["sha256"]:
                raise CollectionError("archive_integrity_failed")
            entries.append((path, path.relative_to(root).as_posix()))
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("xb") as stream:
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path, reference in entries:
                    archive.write(path, reference)
                for name in sorted(normalized["files"]):
                    archive.write(db_directory / name, "db/" + name)
                archive.write(db_directory / "normalized-manifest.json", "db/normalized-manifest.json")
                archive.writestr("collection-status.json", json.dumps(status, ensure_ascii=False, indent=2))
                archive.writestr("summary.md", summary_text(root))
                archive.writestr("manifest.json", json.dumps({"schema_version": "molit_package_v1",
                    "batch_id": plan["batch_id"], "complete": status["complete"],
                    "quality_status": "source_unverified", "format": "xml",
                    "observation_period": [plan["observation_from"], plan["snapshot_date"]],
                    "districts": plan["districts"], "months": plan["months"], "per_page": plan["per_page"],
                    "sources": [{"source_id": SERVICES[s]["source"], "dataset_id": SERVICES[s]["dataset"],
                                 "endpoint": SERVICES[s]["endpoint"], "mapping_version": NORMALIZATION_VERSION}
                                for s in plan["services"]],
                    "counts": normalized["counts"],
                    "files": [{"path": reference, "sha256": digest_file(path)} for path, reference in entries],
                    "derived_files": normalized["files"]}, ensure_ascii=False, indent=2))
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return {"archive": str(output), "sha256": digest_file(output), "complete": status["complete"],
            "record_url": plan["record_url"], "drive_status": "upload_pending"}

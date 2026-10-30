"""Allowlisted offline parsers. Source IDs remain source-specific, never matches."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import sqlite3
import zipfile
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .common import PipelineError, dumps

ADAPTERS = {"molit_xml": "molit_normalization_v1", "statistics_xlsx": "statistics_sources_v1",
            "assessed_csv": "molit_house_price_csv_v1", "neis_json": "neis_schoolinfo_json_v1"}
PRICE_HEADER = ["기준연도", "기준월", "법정동코드", "도로명주소", "시도", "시군구", "읍면", "동리", "특수지코드",
                "본번", "부번", "특수지명", "단지명", "동명", "호명", "전용면적", "공시가격", "단지코드", "동코드", "호코드", "건축물대장PK"]


def arrow_schema(adapter):
    import pyarrow as pa
    fields = [(k, pa.string()) for k in ["record_id", "dataset_id", "mapping_version", "input_id", "source_sha256",
               "source_ref", "section", "quality_status", "payload_json"]]
    fields += [("source_row", pa.int64()), ("source_column", pa.int64())]
    if adapter == "molit_xml":
        fields += [(k, pa.string()) for k in ["source", "sgg_cd", "contract_date", "apartment_name", "source_complex_id"]]
        fields += [(k, pa.int64()) for k in ["deposit_krw", "monthly_rent_krw", "price_krw"]] + [("area_sqm", pa.float64())]
    elif adapter == "statistics_xlsx":
        fields += [(k, pa.string()) for k in ["series_id", "period_key", "value_decimal", "value_status", "unit_code", "dimensions_json", "source_view"]]
    elif adapter == "assessed_csv":
        fields += [(k, pa.string()) for k in ["bjd_cd", "sgg_cd", "assessment_date", "area_sqm", "source_subject_id", "apartment_name"]]
        fields += [("amount_krw", pa.int64())]
    else:
        fields += [(k, pa.string()) for k in ["source_entity_id", "identifier_namespace", "name", "region_name_raw", "road_address_raw", "founded_date"]]
    return pa.schema(fields)


class SampleComplete(Exception):
    pass


class Output:
    def __init__(self, directory, dataset, limit=None):
        import pyarrow as pa
        import pyarrow.parquet as pq
        self.pa = pa
        self.dataset = dataset
        self.limit = limit
        self.schema = arrow_schema(dataset["adapter_id"])
        self.output_fields = tuple(self.schema.names)
        self.identity_prefix = "[" + dumps(dataset["dataset_id"]) + "," + dumps(dataset["mapping_version"]) + ","
        self.writer = pq.ParquetWriter(directory / "data.parquet", self.schema, compression="zstd")
        self.quarantine = (directory / "quarantine.jsonl").open("w", encoding="utf-8", newline="\n")
        self.buffer = []
        self.counts = {k: 0 for k in ["input_rows", "accepted_input_rows", "excluded_rows", "rejected_rows", "output_rows", "lineage_rows"]}
        self.digest = hashlib.sha256()
        self.partial = limit is not None

    def begin(self, source, section, row):
        if self.limit is not None and self.counts["input_rows"] >= self.limit:
            self.partial = True
            raise SampleComplete
        self.counts["input_rows"] += 1

    def emit(self, source, section, row, record, *, status="accepted", reason=None, column=None, count_input=True):
        if count_input:
            self.begin(source, section, row)
            self.counts[status + "_input_rows" if status == "accepted" else status + "_rows"] += 1
        locator = {"input_id": source["input_id"], "source_sha256": source["sha256"],
                   "source_ref": source["descriptor"].get("source_ref", source["input_id"]),
                   "section": section, "source_row": row, "source_column": column}
        # Canonical fragments preserve the prior exact bytes without serializing
        # the same nested record/locator twice for every cell.
        locator_json, record_json = dumps(locator), dumps(record)
        outcome_json = ',"accepted",null,' if status == "accepted" and reason is None else "," + dumps(status) + "," + dumps(reason) + ","
        self.digest.update(("[" + locator_json + outcome_json + record_json + "]\n").encode("utf-8"))
        if status != "accepted":
            # Region-wide exclusions are reproducible from the declared filter and raw hash.
            if reason != "outside_seoul":
                self.quarantine.write(dumps(locator | {"status": status, "reason": reason, "raw": record}) + "\n")
            return
        record_id = hashlib.sha256((self.identity_prefix + locator_json + "]").encode("utf-8")).hexdigest()
        item = locator | {"record_id": record_id,
                          "dataset_id": self.dataset["dataset_id"], "mapping_version": self.dataset["mapping_version"],
                          "quality_status": "source_unverified", "payload_json": record_json}
        item.update({k: record.get(k) for k in self.output_fields if k not in item})
        self.buffer.append(item)
        self.counts["output_rows"] += 1
        self.counts["lineage_rows"] += 1
        if len(self.buffer) >= 10000:
            self.flush()

    def flush(self):
        if self.buffer:
            self.writer.write_table(self.pa.Table.from_pylist(self.buffer, schema=self.schema))
            self.buffer.clear()

    def close(self):
        try:
            self.flush()
        finally:
            self.writer.close()
            self.quarantine.close()


def molit(sources, contract, out, work, engine):
    from ..collection import SERVICES, parse_page
    from ..collection_db import normalize_row
    start, end = contract["observation_from"], contract["snapshot_date"]
    date.fromisoformat(start)
    date.fromisoformat(end)
    if start > end:
        raise PipelineError("invalid_observation_period")
    for source in sources:
        d = source["descriptor"]
        service = d["service"]
        if service not in SERVICES:
            raise PipelineError("invalid_molit_service")
        page = parse_page(Path(source["path"]).read_bytes(), page=d["page"], per_page=d["per_page"], code=d["district"], month=d["month"])
        for rn, raw in enumerate(page["rows"], 1):
            try:
                row = normalize_row(raw, {"source": SERVICES[service]["source"],
                    "source_file_ref": d["source_ref"], "source_content_sha256": source["sha256"], "source_row_number": rn}, rental=service == "rental")
            except ValueError:
                out.emit(source, "items/item", rn, raw, status="rejected", reason="molit_required_value_invalid")
                continue
            if not start <= row["contract_date"] <= end:
                out.emit(source, "items/item", rn, raw, status="excluded", reason="outside_observation_period")
            else:
                out.emit(source, "items/item", rn, row)


def statistics(sources, contract, out, work, engine):
    from ..statistics_storage import _profile, _registry, _rows
    registry = _registry()
    for source in sources:
        path = Path(source["path"])
        profile = _profile(Path(source["descriptor"].get("provided_filename", path.name)), registry)
        for sheet, sid, dimensions, unit, values in _rows(path.read_bytes(), profile):
            if not values:
                continue
            rn = values[0][2]
            out.begin(source, sheet, rn)
            out.counts["accepted_input_rows"] += 1
            dimensions_json = dumps(dimensions)
            for period, header, r, c, raw, state, exact, numeric in values:
                record = {"series_id": sid, "period_key": period, "dimensions_json": dimensions_json,
                          "unit_code": unit, "value_decimal": exact, "value_status": state,
                          "raw_value_json": raw, "source_header_raw": header, "source_view": profile["source_view"],
                          "source_dataset_id": profile["dataset_id"], "unit_status": profile["unit_status"]}
                out.emit(source, sheet, r, record, column=c, count_input=False)


@contextmanager
def csv_stream(source):
    path, d = Path(source["path"]), source["descriptor"]
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            member = d.get("member")
            if not isinstance(member, str) or member not in archive.namelist() or member.endswith("/"):
                raise PipelineError("explicit_zip_member_required")
            with archive.open(member) as stream:
                yield io.TextIOWrapper(stream, encoding=d.get("encoding", "utf-8"), newline="")
    else:
        with path.open(encoding=d.get("encoding", "utf-8"), newline="") as stream:
            yield stream


def price_rows(source, work, engine, limit=None):
    with csv_stream(source) as stream:
        if engine == "python":
            reader = csv.reader(stream)
            if next(reader, None) != PRICE_HEADER:
                raise PipelineError("assessed_header_mismatch")
            for row in reader:
                if len(row) != len(PRICE_HEADER):
                    yield None
                else:
                    yield dict(zip(PRICE_HEADER, row))
        elif engine in {"pandas_full", "pandas_chunked"}:
            import pandas as pd
            options = dict(dtype=str, na_filter=False, keep_default_na=False, on_bad_lines="error", nrows=limit)
            frames = pd.read_csv(stream, **options, chunksize=10000) if engine == "pandas_chunked" else [pd.read_csv(stream, **options)]
            for frame in frames:
                if list(frame.columns) != PRICE_HEADER:
                    raise PipelineError("assessed_header_mismatch")
                yield from frame.to_dict("records")
        elif engine == "duckdb":
            import duckdb
            target = work / "csv-input.csv"
            with target.open("w", encoding="utf-8", newline="") as dest:
                shutil.copyfileobj(stream, dest)
            with duckdb.connect(config={"threads": 1}) as db:
                # Bound path and fixed SQL: Python's relation API uses different CSV option names.
                db.execute("SET autoinstall_known_extensions=false")
                db.execute("SET autoload_known_extensions=false")
                sql = "SELECT * FROM read_csv(?, header=true, all_varchar=true, force_not_null=?, strict_mode=true)"
                params = [str(target), PRICE_HEADER]
                if limit is not None:
                    sql += " LIMIT ?"
                    params.append(limit)
                cursor = db.execute(sql, params)
                names = [c[0] for c in cursor.description]
                if names != PRICE_HEADER:
                    raise PipelineError("assessed_header_mismatch")
                while rows := cursor.fetchmany(10000):
                    for row in rows:
                        yield dict(zip(names, row))
        else:
            raise PipelineError("unsupported_engine")


def assessed(sources, contract, out, work, engine):
    for source in sources:
        section = source["descriptor"].get("member", "csv")
        remaining = None if out.limit is None else max(0, out.limit - out.counts["input_rows"])
        if remaining == 0:
            raise SampleComplete
        for rn, raw in enumerate(price_rows(source, work, engine, remaining), 1):
            if raw is None:
                out.emit(source, section, rn, {}, status="rejected", reason="column_count")
                continue
            bjd = raw["법정동코드"]
            if not (len(bjd) == 10 and bjd.isascii() and bjd.isdigit()):
                out.emit(source, section, rn, raw, status="rejected", reason="invalid_bjd_code")
                continue
            if not bjd.startswith("11"):
                # No payload serialization for millions of rows outside the declared scope.
                out.begin(source, section, rn)
                out.counts["excluded_rows"] += 1
                continue
            try:
                amount = int(raw["공시가격"])
                area = Decimal(raw["전용면적"])
                assessment = date(int(raw["기준연도"]), int(raw["기준월"]), 1).isoformat()
                if not (0 <= amount < 2**63 and area.is_finite() and area > 0 and len(bjd) == 10 and bjd.isascii() and bjd.isdigit()):
                    raise ValueError
            except (ValueError, InvalidOperation, OverflowError):
                out.emit(source, section, rn, raw, status="rejected", reason="invalid_assessed_value")
                continue
            row = {"amount_krw": amount, "area_sqm": format(area, "f"), "assessment_date": assessment,
                   "bjd_cd": bjd, "sgg_cd": bjd[:5], "source_subject_id": ":".join(raw[k] for k in ["단지코드", "동코드", "호코드"]),
                   "subject_namespace": "molit_house_price:complex_dong_ho", "apartment_name": raw["단지명"] or None,
                   "complex_id": None, "building_id": None, "raw_payload": raw}
            out.emit(source, section, rn, row)


def school(sources, contract, out, work, engine):
    clean = lambda v: str(v).strip() or None if v is not None else None
    seen_pages, totals = set(), set()
    for source in sources:
        d = source["descriptor"]
        data = json.loads(Path(source["path"]).read_text(encoding="utf-8"))["schoolInfo"]
        heads = data[0]["head"]
        total = next(h["list_total_count"] for h in heads if "list_total_count" in h)
        result = next(h["RESULT"]["CODE"] for h in heads if "RESULT" in h)
        rows = data[1]["row"]
        page = d["page"]
        if result != "INFO-000" or page in seen_pages or len(rows) != d["expected_rows"]:
            raise PipelineError("neis_page_contract_mismatch")
        seen_pages.add(page)
        totals.add(total)
        for rn, raw in enumerate(rows, 1):
            code, office, name, kind = [clean(raw.get(k)) for k in ["SD_SCHUL_CODE", "ATPT_OFCDC_SC_CODE", "SCHUL_NM", "SCHUL_KND_SC_NM"]]
            status, reason = "accepted", None
            if office == "V10":
                status, reason = "excluded", "overseas_school_out_of_domestic_scope"
            elif kind is None:
                status, reason = "excluded", "not_school_facility_exam_entry"
            elif not code:
                status, reason = "rejected", "missing_source_entity_id"
            elif not name:
                status, reason = "rejected", "missing_name"
            row = {"source_entity_id": code, "identifier_namespace": "neis:sd_schul_code", "name": name,
                   "neis_office_code": office, "facility_type_name_raw": kind, "region_name_raw": clean(raw.get("LCTN_SC_NM")),
                   "road_address_raw": clean(raw.get("ORG_RDNMA")), "latitude": None, "longitude": None,
                   "complex_id": None, "building_id": None, "raw_payload": raw}
            for key, target in [("FOND_YMD", "founded_date"), ("FOAS_MEMRD", "founding_anniversary_date"), ("LOAD_DTM", "source_loaded_date")]:
                value = clean(raw.get(key))
                try:
                    parsed = datetime.strptime(value, "%Y%m%d").date().isoformat() if value and len(value) == 8 else None
                except ValueError:
                    parsed = None
                row[target], row[target + "_raw"] = parsed, value if not parsed else None
            out.emit(source, "schoolInfo[1].row", rn, row, status=status, reason=reason)
    if len(totals) != 1 or contract.get("expected_total_rows") != next(iter(totals)):
        raise PipelineError("neis_total_contract_mismatch")
    if out.counts["input_rows"] != contract["expected_total_rows"]:
        raise PipelineError("neis_incomplete_pages")


def execute_adapter(dataset, sources, directory, *, engine="python", max_input_rows=None):
    if engine != "python" and dataset["adapter_id"] != "assessed_csv":
        raise PipelineError("engine_not_applicable")
    out = Output(directory, dataset, max_input_rows)
    try:
        try:
            {"molit_xml": molit, "statistics_xlsx": statistics, "assessed_csv": assessed, "neis_json": school}[dataset["adapter_id"]](
                sources, dataset["contract"], out, directory, engine)
        except SampleComplete:
            pass
    except Exception as exc:
        code = str(exc) if isinstance(exc, PipelineError) else "adapter_validation_or_io_failed"
        raise PipelineError(code, {"observed_counts": out.counts, "complete": False}) from None
    finally:
        out.close()
    c = out.counts
    if c["input_rows"] != c["accepted_input_rows"] + c["excluded_rows"] + c["rejected_rows"]:
        raise PipelineError("reconciliation_failed")
    if c["rejected_rows"] and dataset["adapter_id"] != "neis_json":
        raise PipelineError("required_values_rejected", {"observed_counts": c, "complete": True})
    if not c["input_rows"]:
        raise PipelineError("empty_input_not_verified_zero")
    return {"counts": c, "result_digest": out.digest.hexdigest(), "coverage": "partial_sample" if out.partial else "declared_inputs",
            "quality_status": "source_unverified", "scope_exclusion_rule": "bjd_cd prefix != 11" if dataset["adapter_id"] == "assessed_csv" else None}

"""Composition root: wire the accepted pure units into the stage/package shells.

Everything configurable comes from mappings/<t_id>.json and mappings/staging_config.json
(frozen by the A/B adjudication). Unit modules are imported lazily so the package stays
importable while late units are still being integrated.
"""
from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from . import contract as C
from ._reuse import read_json
from .base import Outcome
from .stage import StageFile, StageUnits

ContractError = C.ContractError


def _load_resource(name: str) -> dict:
    text = resources.files(__package__).joinpath(f"mappings/{name}").read_text(encoding="utf-8")
    return json.loads(text)


def load_mapping_doc(t_id: str) -> dict:
    return _load_resource(f"{t_id}.json")


def load_staging_config(t_id: str) -> dict:
    config = _load_resource("staging_config.json")["sources"].get(t_id)
    if config is None:
        raise ContractError("staging_config_missing")
    return config


def pick_variant(doc: dict, headers: tuple):
    """The one mapping whose coverage is complete for these headers (frozen variants)."""
    from .core import mapping as H1
    candidates = doc.get("variants") or {"default": doc["mapping"]}
    matches = []
    for name, raw in candidates.items():
        compiled = H1.compile_mapping(raw)
        if H1.header_coverage(compiled, headers)["complete"]:
            matches.append((name, raw))
    if len(matches) != 1:
        raise ContractError("mapping_variant_ambiguous" if matches else "mapping_variant_missing")
    return matches[0]


def make_scope(config: dict):
    policy = (config.get("scope") or {}).get("policy", "always_in")
    if policy == "always_in":
        return lambda fields: "in"
    if policy == "seoul_address_prefix":
        field, prefix = config["scope"]["field"], config["scope"]["prefix"]

        def scope(fields):
            value = fields.get(field)
            if not isinstance(value, str) or not value.strip():
                return "unknown"
            return "in" if value.strip().startswith(prefix) else "out"

        return scope
    raise ContractError("unknown_scope_policy")


def _standardized(fields: dict, coords: dict) -> dict:
    """Fill contract coordinate fields from source_x/source_y per the declared CRS evidence."""
    from .core import coords as C4
    sx, sy = fields.get("source_x"), fields.get("source_y")
    if sx is None and sy is None:
        return fields
    source_crs = coords.get("source_crs")
    if source_crs in (None, "per_file_prj"):
        source_crs = fields.get("source_crs") or "unknown"
    out = dict(fields)
    out.update(C4.standardize(sx, sy, source_crs=source_crs,
                              axis_order=coords.get("axis_order")))
    return out


def make_normalizer(config: dict, spatial_meta: dict | None = None):
    """(fields, envelope) -> Outcome(s), wired to the frozen record_type."""
    settings = config.get("normalize") or {}
    record_type = settings.get("record_type")
    coords = config.get("coords") or {}
    from .normalize import facility, spatial_layer, transit

    if record_type == "facility":
        namespace = settings.get("type_namespace", "unknown")

        def normalize(fields, envelope):
            return facility.normalize_facility(_standardized(fields, coords),
                                               envelope=envelope, type_namespace=namespace)
        return normalize
    if record_type == "transit_route":
        namespace = settings.get("namespace", "unknown")

        def normalize(fields, envelope):
            prepared = dict(fields)
            prepared.setdefault("route_id", fields.get("source_entity_id"))
            prepared.setdefault("route_name", fields.get("name"))
            return transit.normalize_route(prepared, envelope=envelope, namespace=namespace)
        return normalize
    if record_type == "transit_stop_link":
        def normalize(fields, envelope):
            prepared = dict(fields)
            prepared.setdefault("route_id", fields.get("source_route_id"))
            prepared.setdefault("stop_id", fields.get("source_stop_id"))
            return transit.normalize_stop_link(
                prepared, envelope=envelope,
                route_namespace=fields.get("route_namespace") or "unknown",
                stop_namespace=fields.get("stop_namespace") or "unknown")
        return normalize
    if record_type == "time_observation":
        from .core import envelope as C5
        from .core import timefmt as C2
        from .normalize import time_observation as C8
        metric_ns = settings.get("metric_namespace", "metric")
        subject_ns = settings.get("subject_namespace", "unknown")
        table = settings.get("metric_table") or {}
        dt_fmt = settings.get("observed_at_fmt", "%Y-%m-%d %H:%M")
        missing_prefix = settings.get("missing_value_prefix")

        def normalize(fields, envelope):
            code = (fields.get("metric_raw") or "").strip()
            item = table.get(code)
            metric_code = f"{metric_ns}:{item['name']}" if item else f"{metric_ns}:{code}"
            unit_code = item["unit"] if item else "unknown"
            try:
                observed = C2.kst_to_utc_z(fields.get("observed_at_raw") or "", fmt=dt_fmt)
            except ContractError:
                record = C5.finalize({**envelope, **fields}, "rejected",
                                     "invalid_date:observed_at_raw")
                return Outcome(record, "rejected", "invalid_date:observed_at_raw")
            value = fields.get("value_raw")
            if (missing_prefix and isinstance(value, str)
                    and value.strip().startswith(missing_prefix)):
                fields = {**fields, "value_raw": None}
            return C8.normalize_observations(
                fields, envelope=envelope,
                metrics=[{"metric_code": metric_code, "source_field": "value_raw",
                          "unit_code": unit_code}],
                subject_namespace=subject_ns, subject_field="source_subject_id",
                observed_at_utc=observed)
        return normalize
    if record_type == "regional_statistic":
        from .core import timefmt as C2
        from .normalize import regional_statistic as C10
        metric_code = settings.get("metric_code", "metric")
        frequency = settings.get("frequency", "daily")
        unit_code = settings.get("unit_code", "unknown")
        dimension_fields = settings.get("dimension_fields") or {}
        region_fields = tuple(settings.get("region_fields") or ("adm_cd",))
        date_field = settings.get("date_field", "date_raw")

        def normalize(fields, envelope):
            prepared = dict(fields)
            prepared["period_key"] = C2.iso_date(fields.get(date_field))
            dimensions = {name: fields.get(source)
                          for name, source in dimension_fields.items()}
            return C10.normalize_statistic(prepared, envelope=envelope,
                                           metric_code=metric_code, frequency=frequency,
                                           unit_code=unit_code, value_field="value_raw",
                                           region_fields=region_fields,
                                           dimensions=dimensions)
        return normalize
    if record_type == "spatial_layer":
        meta_table = spatial_meta or {}
        event_date_field = settings.get("event_date_field")

        def normalize(fields, envelope):
            meta = meta_table.get(envelope.get("source_file_ref")) or {}
            feature_id = envelope.get("source_feature_id")
            geometry_ref = (f"{meta['shp_ref']}#record={feature_id}"
                            if meta.get("shp_ref") else None)
            return spatial_layer.normalize_feature(
                fields, envelope=envelope,
                layer_id=meta.get("layer_id") or settings.get("layer_id", "layer"),
                representation=settings.get("representation", "vector"),
                geometry_ref=geometry_ref,
                source_crs=meta.get("crs") or "unknown",
                bbox=(meta.get("bbox") or {}).get(feature_id),
                event_date=fields.get(event_date_field) if event_date_field else None)
        return normalize
    raise ContractError("unsupported_record_type_wiring")


def stage_units(normalize) -> StageUnits:
    from .core import envelope as C5
    from .core import mapping as H1
    return StageUnits(compile_mapping=H1.compile_mapping, apply_mapping=H1.apply_mapping,
                      header_coverage=H1.header_coverage, make_envelope=C5.make_envelope,
                      finalize=C5.finalize, normalize=normalize)


def code_signature() -> str:
    """Hash of the staging-relevant sources: a change forces a new batch (plan §5)."""
    import hashlib
    import sys
    from . import stage as stage_module
    from .core import envelope, mapping
    from .normalize import facility, regional_statistic, spatial_layer, time_observation, transit
    digest = hashlib.sha256()
    for module in (mapping, envelope, facility, transit, time_observation, spatial_layer,
                   regional_statistic, stage_module, sys.modules[__name__]):
        digest.update(Path(module.__file__).read_bytes())
    return digest.hexdigest()


def package_units():
    from .package import manifest_doc, record_check, schema_doc, validation_doc, zipper
    from .package_build import PackageUnits
    return PackageUnits(build_schema=schema_doc.build_schema,
                        build_manifest=manifest_doc.build_manifest,
                        secret_shapes=manifest_doc.secret_shapes,
                        reconcile=validation_doc.reconcile,
                        build_validation=validation_doc.build_validation,
                        check_records=record_check.check_records,
                        write_zip=zipper.write_zip, split_parts=zipper.split_parts)


def dataset_meta(plan: dict, *, registry_source: dict, mapping_version: str,
                 collected: str, period: str, region: str, kind: str, provider_slug: str) -> dict:
    """The P2 dataset dict plus the deterministic zip name (C1 naming rules)."""
    from .core import ids
    zip_name = ids.zip_name(provider=provider_slug, kind=kind, region=region, period=period,
                            collected=collected, batch_id=plan["batch_id"])
    return {"name": registry_source["title"], "provider": registry_source["provider"],
            "source": registry_source["documentation_url"],
            "mapping_version": mapping_version,
            "collection_method": "keyless HTTPS GET via budongi.team_collection cli fetch-files "
                                 "(journalled, sha256 per payload)",
            "scope": (load_staging_config(plan["t_id"]).get("scope") or {}).get("evidence", ""),
            "request": "; ".join(r["request_id"] for r in plan["requests"]),
            "expected_rows": next((r.get("expected_rows") for r in plan["requests"]), None),
            "zip_name": zip_name}


def readme_text(plan: dict, *, registry_source: dict, staging: dict, mapping_version: str) -> str:
    """Korean offline reproduction note packaged as README.md."""
    sections = staging.get("sections", [])
    lines = [f"# {registry_source['title']} — team_collection_v1 패키지", "",
             f"- source_id: {plan['source_id']} / batch_id: {plan['batch_id']}",
             f"- 수집 Issue: {plan['record_url']}",
             f"- 제공처 문서: {registry_source['documentation_url']}",
             f"- mapping_version: {mapping_version} (code/mapping.json)",
             f"- staged_at_utc: {staging.get('staged_at_utc')}", "",
             "## 재현 (오프라인)", "",
             "1. `collection/plan.json`의 요청과 `collection/requests/*.json` 저널로 raw 파일의",
             "   sha256·수집 시각을 대조한다 (재다운로드 없이 검증 가능).",
             "2. `code/mapping.json`을 budongi.team_collection.core.mapping.compile_mapping에",
             "   넣고 raw를 같은 reader 설정(code/staging.json)으로 읽으면",
             "   `normalized/*.jsonl`이 바이트 단위로 재생성된다.",
             "3. `validation.json`의 섹션 합계와 manifest counts가 일치해야 한다.", "",
             "## 건수", ""]
    for section in sections:
        lines.append(f"- {section['section']}: raw {section['raw']} = accepted "
                     f"{section['accepted']} + excluded {section['excluded']} + rejected "
                     f"{section['rejected']}")
    lines += ["", f"- 정규화 JSONL 줄 수: {staging.get('jsonl_lines')}",
              "", "담당: " + C.OWNER]
    return "\n".join(lines) + "\n"


def batch_context(plan: dict, *, staged_at_utc: str):
    from .core.envelope import BatchContext
    doc = load_mapping_doc(plan["t_id"])
    variants = doc.get("variants")
    mapping_version = (doc["mapping"]["mapping_version"] if not variants
                       else sorted(v["mapping_version"] for v in variants.values())[0])
    return BatchContext(source_id=plan["source_id"], batch_id=plan["batch_id"],
                        mapping_version=mapping_version, record_type=plan["record_type"],
                        staged_at_utc=staged_at_utc)


def xlsx_files(batch_dir: Path, plan: dict, config: dict) -> list[StageFile]:
    """StageFile list for the xlsx/csv readers (pilot lanes); SHP batches get their own builder."""
    from .readers import csvread, xlsxread
    reader = config["reader"]
    doc_files = set(reader.get("doc_files") or ())
    files = []
    for item in plan["requests"]:
        journal_path = Path(batch_dir) / "raw" / item["request_id"] / "journal.json"
        if not journal_path.is_file():
            continue
        journal = read_json(journal_path)
        for page in journal["pages"]:
            original = page.get("original_name") or page["file"]
            if original in doc_files:
                continue
            path = journal_path.parent / page["file"]
            section = reader.get("section", "data")
            if reader["kind"] == "xlsx":
                def read(p=path):
                    return xlsxread.read_xlsx(p, sheet=reader["sheet"],
                                              header_row=reader.get("header_row", 1),
                                              section=section)
            elif reader["kind"] == "csv":
                def read(p=path):
                    encoding = _sniff_encoding(p)
                    return csvread.read_csv(p, encoding=encoding, section=section,
                                            header_row=reader.get("header_row", 1))
            else:
                raise ContractError("unsupported_reader_kind")
            files.append(StageFile(file_ref=f"raw/{item['request_id']}/{page['file']}",
                                   sha256=page["sha256"], section=section, read=read))
    if not files:
        raise ContractError("no_staged_files")
    return files


def zip_csv_files(batch_dir: Path, plan: dict, config: dict, workdir: Path) -> list[StageFile]:
    """StageFiles for batches whose raw payloads are ZIPs each holding CSV members."""
    from .readers import csvread
    from .readers import zipguard as E3
    reader = config["reader"]
    section = reader.get("section", "data")
    files = []
    for item in plan["requests"]:
        journal_path = Path(batch_dir) / "raw" / item["request_id"] / "journal.json"
        if not journal_path.is_file():
            continue
        journal = read_json(journal_path)
        for page in journal["pages"]:
            zip_path = journal_path.parent / page["file"]
            members = [m["name"] for m in E3.list_members(zip_path)
                       if m["name"].lower().endswith(".csv")]
            if len(members) != 1:
                raise ContractError("zip_csv_member_count")
            work = Path(workdir) / item["request_id"] / Path(page["file"]).stem
            work.mkdir(parents=True, exist_ok=True)
            extracted = E3.extract_member(zip_path, members[0], work, max_bytes=1 << 31)

            def read(path=extracted):
                return csvread.read_csv(path, encoding=_sniff_encoding(path),
                                        section=section,
                                        header_row=reader.get("header_row", 1))

            files.append(StageFile(file_ref=f"raw/{item['request_id']}/{page['file']}",
                                   sha256=page["sha256"], section=section, read=read))
    if not files:
        raise ContractError("no_staged_files")
    return files


def shp_files(batch_dir: Path, plan: dict, config: dict, doc: dict,
              workdir: Path) -> tuple[list[StageFile], dict]:
    """StageFiles plus per-file spatial metadata for shp_zip batches (variant per file)."""
    import re
    from .core import coords as C4
    from .readers import dbf as E4
    from .readers import shp as H4
    from .readers import zipguard as E3
    reader = config["reader"]
    section_tpl = reader.get("section", "layer")
    files, meta = [], {}
    for item in plan["requests"]:
        journal_path = Path(batch_dir) / "raw" / item["request_id"] / "journal.json"
        if not journal_path.is_file():
            continue
        journal = read_json(journal_path)
        for page in journal["pages"]:
            zip_path = journal_path.parent / page["file"]
            original = page.get("original_name") or page["file"]
            file_ref = f"raw/{item['request_id']}/{page['file']}"
            members = {m["name"]: m for m in E3.list_members(zip_path)}
            by_ext = {}
            for name in members:
                ext = name.rsplit(".", 1)[-1].lower()
                if ext in ("shp", "shx", "dbf", "prj", "cpg"):
                    if ext in by_ext:
                        raise ContractError(f"shp_zip_duplicate_member:{ext}")
                    by_ext[ext] = name
            for required in ("shp", "shx", "dbf"):
                if required not in by_ext:
                    raise ContractError(f"shp_zip_member_missing:{required}")
            work = Path(workdir) / item["request_id"] / Path(page["file"]).stem
            work.mkdir(parents=True, exist_ok=True)
            extracted = {ext: E3.extract_member(zip_path, name, work, max_bytes=1 << 29)
                         for ext, name in by_ext.items()}
            crs = "unknown"
            if "prj" in extracted:
                crs = C4.epsg_from_prj(extracted["prj"].read_text(encoding="ascii",
                                                                  errors="replace")) or "unknown"
            encoding = "cp949"
            if "cpg" in extracted:
                declared = extracted["cpg"].read_text(encoding="ascii", errors="replace").strip()
                encoding = {"utf-8": "utf-8", "utf8": "utf-8", "949": "cp949", "cp949": "cp949",
                            "euc-kr": "cp949", "uhc": "cp949"}.get(declared.lower(), "cp949")
            dbf_bytes = extracted["dbf"].read_bytes()
            header_doc = E4.dbf_header(dbf_bytes, encoding=encoding)
            field_names = tuple(f["name"] for f in header_doc["fields"])
            bbox = {}
            shp_bytes, shx_bytes = extracted["shp"].read_bytes(), extracted["shx"].read_bytes()
            for record in H4.iter_shp_records(shp_bytes, shx_bytes):
                bbox[str(record["number"])] = record["bbox"]
            if header_doc["record_count"] != len(bbox):
                raise ContractError("shp_dbf_record_mismatch")
            year = (re.search(r"(20\d\d)", original) or [None, "all"])[1]
            section = section_tpl.format(year=year) if "{year}" in section_tpl else section_tpl
            layer_tpl = (config.get("normalize") or {}).get("layer_id", "layer")
            layer_id = layer_tpl.format(year=year) if "{year}" in layer_tpl else layer_tpl
            _, variant_mapping = pick_variant(doc, field_names)

            strict = True
            try:
                for _ in E4.iter_dbf(dbf_bytes, encoding=encoding):
                    pass
            except ContractError as exc:
                if str(exc) != "decode_error":
                    raise
                strict = False   # known source defect: a few cells are not decodable

            def read(data=dbf_bytes, enc=encoding, names=field_names, sec=section,
                     use_strict=strict):
                def rows():
                    if use_strict:
                        for number, deleted, values in E4.iter_dbf(data, encoding=enc):
                            if deleted:
                                raise ContractError("dbf_deleted_record")
                            yield _raw_row(sec, number, tuple(values.get(n) for n in names))
                    else:
                        yield from _tolerant_dbf_rows(data, enc, sec)
                return names, rows()

            files.append(StageFile(file_ref=file_ref, sha256=page["sha256"], section=section,
                                   read=read, position_kind="feature",
                                   mapping_doc=variant_mapping))
            meta[file_ref] = {"shp_ref": f"{file_ref}#{by_ext['shp']}", "crs": crs,
                              "bbox": bbox, "layer_id": layer_id}
    if not files:
        raise ContractError("no_staged_files")
    return files, meta


def _raw_row(section: str, position: int, values: tuple):
    from .base import RawRow
    return RawRow(section, position, values)


def _tolerant_dbf_rows(data: bytes, encoding: str, section: str):
    """Fallback for a dBASE file whose odd cells are not decodable (observed: 2022 flood
    F_ZONE_NM, 36/19,881 records). Rows with a corrupt cell become ragged -> rejected with
    replacement characters; the true bytes stay in the packaged raw ZIP."""
    import struct
    from .base import RawRow
    records, header_len, record_len = struct.unpack("<IHH", data[4:12])
    fields, offset = [], 32
    while offset + 32 <= header_len - 1 and data[offset] != 0x0D:
        raw = data[offset:offset + 32]
        fields.append((raw[:11].split(b"\x00")[0].decode(encoding, "replace"), raw[16]))
        offset += 32
    position = header_len
    for number in range(1, records + 1):
        record = data[position:position + record_len]
        position += record_len
        if record[:1] == b"*":
            raise ContractError("dbf_deleted_record")
        cell_offset, values, corrupt = 1, [], False
        for _name, length in fields:
            chunk = record[cell_offset:cell_offset + length]
            cell_offset += length
            try:
                text = chunk.decode(encoding)
            except UnicodeDecodeError:
                text = chunk.decode(encoding, "replace")
                corrupt = True
            text = text.strip()
            values.append(text if text else None)
        if corrupt:
            yield RawRow(section, number, tuple(values), status="ragged", reason="ragged_row")
        else:
            yield RawRow(section, number, tuple(values))


QUOTA_CAPS = {"airkorea": 500, "datagokr": 10000, "seoul": 1000, "topis": 1000}
LANE_RATES = {"B": (2.0, 0.2, 5.0), "C": (1.0, 0.2, 2.0), "D": (1.0, 0.2, 3.0)}


def quota_cap(bucket: str) -> int:
    return QUOTA_CAPS.get((bucket or "").split(":")[0], 1000)


def _seoul_service(template: str) -> str:
    parts = template.split("/json/", 1)
    if len(parts) != 2:
        raise ContractError("unsupported_template")
    return parts[1].split("/", 1)[0]


def lane_units(lane: str, *, registry: dict, origin: str):
    """LaneUnits for one keyed batch: journal H2, pacing E5, transport, adapter, classify E6."""
    import time
    from datetime import datetime, timezone
    from . import transport
    from ._reuse import no_proxy_opener, utc_z
    from .adapters import datagokr as E8
    from .adapters import seoul as E7
    from .registry import http_acknowledged
    from .runtime import classify as E6
    from .runtime.journal import RequestJournal
    from .runtime.ratelimit import Aimd, TokenBucket
    from .supervisor import LaneUnits
    start, floor, ceiling = LANE_RATES.get(lane, (1.0, 0.2, 2.0))
    bucket = TokenBucket(start, 1, clock=time.monotonic, sleep=time.sleep)
    aimd = Aimd(start, floor, ceiling)
    opener = no_proxy_opener()
    allow_http = http_acknowledged(registry, origin)
    is_seoul = ":8088" in origin

    def fetch(spec, handle):
        return transport.fetch_page(spec, handle, opener=opener, allow_http=allow_http)

    def parse(spec, payload):
        if is_seoul:
            page, code = E7.parse_page(payload, service=_seoul_service(spec.url_template))
            return page, code, ""
        page, code = E8.parse_page(payload)
        return page, code, ""

    def classify(spec, code, message):
        return E6.classify_seoul(code) if is_seoul else E6.classify_datagokr(code)

    def make_pages(spec, total):
        if total is None:
            return []
        if is_seoul:
            windows = E7.window_params(int(total))
            return [(index + 1,
                     _replace_spec(spec, url_template=spec.url_template.replace(
                         "/1/1000/", f"/{start_row}/{end_row}/", 1)))
                    for index, (start_row, end_row) in enumerate(windows) if index > 0]
        pages = E8.page_count(int(total), rows=100)
        out = []
        for number in range(2, pages + 1):
            params = tuple(("pageNo", str(number)) if name == "pageNo" else (name, value)
                           for name, value in spec.params)
            out.append((number, _replace_spec(spec, params=params)))
        return out

    return LaneUnits(journal=lambda folder, request: RequestJournal(
                         folder, request, clock=utc_z),
                     bucket=lambda _origin: bucket, aimd=lambda _origin: aimd,
                     fetch=fetch, parse=parse, classify=classify, make_pages=make_pages)


def _replace_spec(spec, **changes):
    from dataclasses import replace
    return replace(spec, **changes)


def _sniff_encoding(path: Path) -> str:
    head = Path(path).read_bytes()[:65536]
    for encoding in ("utf-8-sig", "cp949"):
        try:
            head.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    raise ContractError("decode_error")

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


def make_normalizer(config: dict):
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
            return transit.normalize_stop_link(
                fields, envelope=envelope,
                route_namespace=fields.get("route_namespace") or "unknown",
                stop_namespace=fields.get("stop_namespace") or "unknown")
        return normalize
    if record_type == "spatial_layer":
        def normalize(fields, envelope):
            return spatial_layer.normalize_feature(
                _standardized(fields, coords), envelope=envelope,
                layer_id=envelope.get("_layer_id") or settings.get("layer_id", "layer"),
                representation=settings.get("representation", "vector"),
                geometry_ref=envelope.get("_geometry_ref") or "",
                source_crs=envelope.get("_source_crs") or "unknown",
                bbox=envelope.get("_bbox"))
        return normalize
    raise ContractError("unsupported_record_type_wiring")


def stage_units() -> StageUnits:
    from .core import envelope as C5
    from .core import mapping as H1
    return StageUnits(compile_mapping=H1.compile_mapping, apply_mapping=H1.apply_mapping,
                      header_coverage=H1.header_coverage, make_envelope=C5.make_envelope,
                      finalize=C5.finalize, normalize=None)  # normalize is bound per batch


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


def _sniff_encoding(path: Path) -> str:
    head = Path(path).read_bytes()[:65536]
    for encoding in ("utf-8-sig", "cp949"):
        try:
            head.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    raise ContractError("decode_error")

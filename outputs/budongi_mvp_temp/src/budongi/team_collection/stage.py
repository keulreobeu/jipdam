"""Batch staging shell (L2): raw rows -> mapped, normalized JSONL plus counted excluded rows.

The pure units (mapping, envelope, normalizers, readers) are injected so the engine is
testable before they integrate; cli wires the real modules. Staging is idempotent per
input signature: the same inputs stage zero new rows, changed inputs need a new batch.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from . import contract as C
from ._reuse import read_json, safe_file, utc_z, write_json

ContractError = C.ContractError
STAGING_SCHEMA = "role2_staging_v1"


@dataclass(frozen=True)
class StageUnits:
    """The pure callables stage_batch composes (H1, C5 and one normalizer wrapper)."""
    compile_mapping: Callable
    apply_mapping: Callable          # (mapping, header, values) -> (fields, [error codes])
    header_coverage: Callable        # (mapping, headers) -> {"complete": bool, ...}
    make_envelope: Callable          # (ctx, *, file_ref, file_sha, section, position|feature_id)
    finalize: Callable               # (record, status, reason) -> record
    normalize: Callable              # (fields, envelope) -> Outcome | iterable of Outcome


@dataclass(frozen=True)
class StageFile:
    """One raw payload to stage; read() yields (header, iterator of RawRow)."""
    file_ref: str                    # batch-relative path, e.g. "raw/r1/p000001_a000001.csv"
    sha256: str
    section: str
    read: Callable
    position_kind: str = "row"       # "row" -> source_row_number, "feature" -> source_feature_id
    mapping_doc: dict | None = None  # per-file variant; None uses the batch mapping


def input_signature(*, batch_id: str, mapping_doc: dict, files, code_signature: str) -> str:
    """Changes when the plan identity, any raw byte, the mapping or the staging code changes."""
    doc = {"batch_id": batch_id, "mapping": mapping_doc, "code": code_signature,
           "raw": sorted((f.file_ref, f.sha256) for f in files)}
    return hashlib.sha256(json.dumps(doc, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _dump(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def _replace(partial: Path, final: Path) -> None:
    final.parent.mkdir(parents=True, exist_ok=True)
    os.replace(partial, final)


def stage_batch(batch_dir: Path, *, ctx, record_type: str, mapping_doc: dict, files,
                units: StageUnits, scope: Callable[[dict], str], code_signature: str,
                clock=utc_z) -> dict:
    """Stage every file of one batch once; a rerun with identical inputs changes nothing."""
    batch_dir = Path(batch_dir)
    if record_type not in C.RECORD_TYPES:
        raise ContractError("invalid_record_type")
    signature = input_signature(batch_id=ctx.batch_id, mapping_doc=mapping_doc, files=files,
                                code_signature=code_signature)
    staging_path = batch_dir / "staging.json"
    if staging_path.exists():
        existing = read_json(staging_path)
        if existing.get("input_signature") != signature:
            raise ContractError("input_changed_use_new_batch")
        return {**existing, "resumed": True, "new_rows": 0}
    mapping = units.compile_mapping(mapping_doc)
    jsonl_path = safe_file(batch_dir, f"normalized/{record_type}.jsonl")
    excluded_path = safe_file(batch_dir, "validation/excluded.csv.gz")
    jsonl_partial, excluded_partial = Path(f"{jsonl_path}.part"), Path(f"{excluded_path}.part")
    for leftover in (jsonl_partial, excluded_partial):
        leftover.parent.mkdir(parents=True, exist_ok=True)
        leftover.unlink(missing_ok=True)
    sections: dict[str, dict] = {}
    jsonl_lines = 0
    with jsonl_partial.open("w", encoding="utf-8", newline="\n") as jsonl, \
            excluded_partial.open("wb") as raw_gz, \
            gzip.GzipFile(fileobj=raw_gz, mode="wb", filename="", mtime=0) as gz_bytes, \
            io.TextIOWrapper(gz_bytes, encoding="utf-8", newline="") as gz_text:
        excluded_rows = csv.writer(gz_text, lineterminator="\n")
        excluded_rows.writerow(["file_ref", "section", "position", "reason", "values_json"])

        def exclude(item: StageFile, position: int, reason: str, values) -> None:
            excluded_rows.writerow([item.file_ref, item.section, position, reason,
                                    json.dumps(list(values), ensure_ascii=False)])

        def emit(record: dict, status: str) -> None:
            nonlocal jsonl_lines
            if status not in C.JSONL_STATUSES:
                raise ContractError("invalid_outcome_status")
            jsonl.write(_dump(record) + "\n")
            jsonl_lines += 1

        for item in files:
            stats = sections.setdefault(item.section, {"section": item.section, "raw": 0,
                                                       "accepted": 0, "excluded": 0, "rejected": 0})
            header, rows = item.read()
            file_mapping = (units.compile_mapping(item.mapping_doc)
                            if item.mapping_doc is not None else mapping)
            coverage = units.header_coverage(file_mapping, header)
            if not coverage["complete"]:
                raise ContractError(f"mapping_incomplete:{item.section}")
            for row in rows:
                stats["raw"] += 1
                position = {"position": row.position} if item.position_kind == "row" \
                    else {"feature_id": str(row.position)}
                if row.status == "blank":
                    stats["excluded"] += 1
                    exclude(item, row.position, row.reason or "blank_row", row.values)
                    continue
                envelope = units.make_envelope(ctx, file_ref=item.file_ref, file_sha=item.sha256,
                                               section=item.section, **position)
                if row.status == "ragged":
                    record = dict(envelope)
                    record["source_cells_json"] = json.dumps(list(row.values), ensure_ascii=False)
                    emit(units.finalize(record, "rejected", row.reason or "ragged_row"), "rejected")
                    stats["rejected"] += 1
                    continue
                fields, errors = units.apply_mapping(file_mapping, header, row.values)
                if errors:
                    record = {**envelope, **fields}
                    emit(units.finalize(record, "rejected", errors[0]), "rejected")
                    stats["rejected"] += 1
                    continue
                verdict = scope(fields)
                if verdict != "in":
                    reason = "out_of_scope_region" if verdict == "out" else "scope_undetermined"
                    stats["excluded"] += 1
                    exclude(item, row.position, reason, row.values)
                    continue
                outcomes = units.normalize(fields, envelope)
                for outcome in ([outcomes] if hasattr(outcomes, "record") else list(outcomes)):
                    if outcome.status == "excluded":
                        stats["excluded"] += 1
                        exclude(item, row.position, outcome.reason or "scope_undetermined", row.values)
                        continue
                    emit(outcome.record, outcome.status)
                    stats[outcome.status] += 1
    summary = {"schema": STAGING_SCHEMA, "input_signature": signature, "batch_id": ctx.batch_id,
               "record_type": record_type, "staged_at_utc": ctx.staged_at_utc or clock(),
               "sections": [sections[name] for name in sections], "jsonl_lines": jsonl_lines,
               "files": [{"file_ref": f.file_ref, "sha256": f.sha256, "section": f.section}
                         for f in files]}
    _replace(jsonl_partial, jsonl_path)
    _replace(excluded_partial, excluded_path)
    write_json(staging_path, summary)  # last write commits the staging
    return {**summary, "resumed": False, "new_rows": jsonl_lines}

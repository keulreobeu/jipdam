"""Batch packaging shell (L3): staged outputs -> one deterministic team_collection_v1 ZIP.

Composes the pure package units (schema/manifest/validation builders, record check,
deterministic zipper, parts splitter) plus the secret sweep. Units are injected so the
shell tests run on fakes before the outsourced units integrate; cli wires the real ones.
Restricted licenses (contract.RESTRICTED_LICENSES) withhold the normalized JSONL from
the shared ZIP; the builder then packages raw + documents only.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import contract as C
from ._reuse import digest_file, read_json, safe_file
from .secret_sweep import sweep_tree, sweep_zip

ContractError = C.ContractError


@dataclass(frozen=True)
class PackageUnits:
    """Pure callables build_package composes (P1-P5 and, optionally later, H5)."""
    build_schema: Callable
    build_manifest: Callable     # P2 build_manifest(plan, *, requests, files, counts, ...)
    secret_shapes: Callable      # P2: (obj) -> list of suspicious value paths
    reconcile: Callable          # P3: (stats) -> list of error codes
    build_validation: Callable   # P3: (stats) -> dict
    check_records: Callable      # P4: (lines, *, manifest, files) -> {"ok", "errors", "counts"}
    write_zip: Callable          # P5: (src, dest, *, arc_root, stamp) -> dict
    split_parts: Callable        # P5: (path, *, part_bytes) -> dict


def _dump_json(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _copy(source: Path, tree: Path, rel: str, files: dict, **extra) -> None:
    target = safe_file(tree, rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    files[rel] = {"path": rel, "bytes": target.stat().st_size, "sha256": digest_file(target),
                  **extra}


def _write(payload: bytes, tree: Path, rel: str, files: dict, **extra) -> None:
    target = safe_file(tree, rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    files[rel] = {"path": rel, "bytes": len(payload), "sha256": digest_file(target), **extra}


def collect_raw(batch_dir: Path, plan: dict) -> tuple[list, list]:
    """(raw payload copies, manifest request docs) from every request journal of the batch."""
    copies, requests = [], []
    for item in plan["requests"]:
        rid = item["request_id"]
        journal_path = Path(batch_dir) / "raw" / rid / "journal.json"
        if not journal_path.is_file():
            requests.append({"request_id": rid, "collection_status": "not_collected",
                             "section": item.get("section", ""), "pages": 0, "received_rows": 0,
                             "expected_rows": item.get("expected_rows"), "error": None})
            continue
        journal = read_json(journal_path)
        copies.append((journal_path, f"collection/requests/{rid}.json", {}))
        rows = 0
        for page in journal["pages"]:
            suffix = page["file"].rsplit(".", 1)[-1].lower() if "." in page["file"] else "bin"
            copies.append((journal_path.parent / page["file"], f"raw/{rid}/{page['file']}",
                           {"format": suffix, "section": item.get("section", ""),
                            "rows": page.get("rows"), "encoding": None}))
            rows += page.get("rows") or 0
        requests.append({"request_id": rid, "collection_status": journal["status"],
                         "section": item.get("section", ""), "pages": len(journal["pages"]),
                         "received_rows": rows, "expected_rows": item.get("expected_rows"),
                         "expected_basis": item.get("expected_basis"), "error": journal.get("error")})
    return copies, requests


def build_package(batch_dir: Path, out_dir: Path, *, plan: dict, staging: dict,
                  schema_inputs: dict, dataset: dict, units: PackageUnits, keys: list[str],
                  readme: str, extra_files: dict[str, bytes] | None = None,
                  stamp: tuple[int, int, int, int, int, int], owner: str = C.OWNER,
                  part_bytes: int = C.PART_BYTES) -> dict:
    """Assemble, document, gate and zip one batch. Deterministic for identical inputs."""
    batch_dir, out_dir = Path(batch_dir), Path(out_dir)
    source_id, batch_id = plan["source_id"], plan["batch_id"]
    record_type, license_doc = plan["record_type"], plan.get("license") or {}
    withheld = (license_doc.get("class") in C.RESTRICTED_LICENSES)
    arc_root = f"{source_id}/{batch_id}"
    tree = out_dir / "tree" / source_id / batch_id
    if tree.exists():
        raise ContractError("package_tree_exists")
    tree.mkdir(parents=True)
    files: dict[str, dict] = {}

    copies, requests = collect_raw(batch_dir, plan)
    for source, rel, extra in copies:
        _copy(source, tree, rel, files, **extra)
    _copy(batch_dir / "plan.json", tree, "collection/plan.json", files)
    jsonl_path = batch_dir / "normalized" / f"{record_type}.jsonl"
    jsonl_lines: list[str] = []
    if record_type != C.RAW_ONLY:
        jsonl_lines = jsonl_path.read_text(encoding="utf-8").splitlines()
        if not withheld:
            _copy(jsonl_path, tree, f"normalized/{record_type}.jsonl", files,
                  format="jsonl", rows=len(jsonl_lines))
        excluded = batch_dir / "validation" / "excluded.csv.gz"
        if excluded.is_file():
            _copy(excluded, tree, "validation/excluded.csv.gz", files, format="csv.gz")
    _write(readme.encode("utf-8"), tree, "README.md", files)
    for rel, payload in sorted((extra_files or {}).items()):
        _write(payload, tree, rel, files)

    sections = staging.get("sections", [])
    counts = {"raw_rows": sum(s["raw"] for s in sections),
              "accepted": sum(s["accepted"] for s in sections),
              "excluded": sum(s["excluded"] for s in sections),
              "rejected": sum(s["rejected"] for s in sections),
              "expected_rows": dataset.get("expected_rows")}
    stats = {"lane": plan["lane"], "source_id": source_id, "batch_id": batch_id,
             "mapping_version": dataset["mapping_version"], "sections": sections,
             "jsonl_lines": len(jsonl_lines), "requests": requests,
             "validated_at_utc": staging.get("staged_at_utc")}
    problems = units.reconcile(stats)
    if problems:
        raise ContractError(f"reconcile_failed:{problems[0]}")
    _write(_dump_json(units.build_validation(stats)), tree, "validation.json", files)
    _write(_dump_json(units.build_schema(**schema_inputs)), tree, "schema.json", files)

    manifest = units.build_manifest(
        plan, requests=requests, files=sorted(files.values(), key=lambda f: f["path"]),
        counts=counts, owner=owner, dataset=dataset, license=license_doc,
        staged_at_utc=staging["staged_at_utc"], normalized_withheld=withheld)
    if units.secret_shapes(manifest):
        raise ContractError("manifest_secret_shape")
    checked = units.check_records(jsonl_lines, manifest=manifest,
                                  files={f["path"]: f for f in files.values()})
    if not checked["ok"]:
        raise ContractError(f"record_check_failed:{checked['errors'][0]}")
    manifest_target = safe_file(tree, "manifest.json")
    manifest_target.write_bytes(_dump_json(manifest))

    if sweep_tree(tree, keys):
        raise ContractError("secret_in_package_tree")
    zip_path = out_dir / dataset["zip_name"]
    if zip_path.exists():
        raise ContractError("package_zip_exists")
    written = units.write_zip(tree, zip_path, arc_root=arc_root, stamp=stamp)
    if sweep_zip(zip_path, keys):
        raise ContractError("secret_in_package_zip")
    report = {"zip": str(zip_path), "zip_name": dataset["zip_name"], "arc_root": arc_root,
              "bytes": zip_path.stat().st_size, "sha256": digest_file(zip_path),
              "counts": counts, "jsonl_lines": len(jsonl_lines), "requests": requests,
              "normalized_withheld": withheld, "written": written, "parts": None}
    if report["bytes"] >= part_bytes:
        report["parts"] = units.split_parts(zip_path, part_bytes=part_bytes)
    return report

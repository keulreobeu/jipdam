"""python -m budongi.team_collection <command> — role-2 collection CLI (ROLE2-COLLECT-001).

Exit codes: 0 done, 2 contract error (nothing fetched), 3 incomplete (resume later).
JSON result on stdout, JSON-lines progress on stderr; neither ever contains keys or URLs with keys.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path

from . import contract as C
from ._reuse import file_opener, process_alive, read_json, utc_z
from .filefetch import fetch_file, ingest_provided, recover, verify
from .registry import check_fetch_gate, load_plan, load_registry, make_plan, spec_from_plan, write_plan

ContractError = C.ContractError


def _lock(batch_dir: Path) -> Path:
    path = batch_dir / ".fetch.lock"
    try:
        handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            pid = int(path.read_text(encoding="ascii").strip() or 0)
        except (OSError, ValueError):
            pid = 0
        if pid and process_alive(pid):
            raise ContractError("collection_in_use") from None
        path.unlink(missing_ok=True)  # the owner process is gone: the lock is stale
        handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(handle, str(os.getpid()).encode("ascii"))
    os.close(handle)
    return path


def _batch_dir(data_root: Path, plan: dict) -> Path:
    data_root.mkdir(parents=True, exist_ok=True)
    taken = sorted(p for p in data_root.glob(f"{plan['t_id']}-*") if (p / "plan.json").is_file())
    for folder in taken:
        if read_json(folder / "plan.json").get("batch_id") == plan["batch_id"]:
            return folder
    return data_root / f"{plan['t_id']}-{len(taken) + 1}"


def _progress(**fields) -> None:
    print(json.dumps(fields, ensure_ascii=False), file=sys.stderr, flush=True)


def cmd_plan(args) -> dict:
    registry = load_registry(args.registry)
    plan = make_plan(registry, args.source, batch_id=args.batch_id, record_url=args.record_url)
    folder = _batch_dir(Path(args.data_root), plan)
    summary = {"t_id": plan["t_id"], "source_id": plan["source_id"], "batch_id": plan["batch_id"],
               "lane": plan["lane"], "record_type": plan["record_type"], "requests": len(plan["requests"]),
               "batch_dir": str(folder)}
    if args.dry_run:
        return {"status": "dry_run", **summary}
    write_plan(folder, plan)
    return {"status": "planned", **summary}


def cmd_fetch_files(args) -> dict:
    registry = load_registry(args.registry)
    folder = Path(args.batch_dir)
    plan = load_plan(folder)
    source = check_fetch_gate(registry, plan)
    if plan["lane"] not in C.FILE_LANES:
        raise ContractError("not_a_file_lane")
    hosts = {urllib.parse.urlsplit(o).hostname for o in source.get("origin_allowlist", [])}
    opener = file_opener(hosts)
    lock = _lock(folder)
    results = []
    try:
        for index, item in enumerate(plan["requests"]):
            if args.limit is not None and index >= args.limit:
                break
            spec = spec_from_plan(item)
            try:
                journal = fetch_file(spec, folder, opener=opener)
                page = journal["pages"][-1]
                results.append({"request_id": spec.request_id, "status": journal["status"],
                                "bytes": page["bytes"], "sha256": page["sha256"]})
            except ContractError as exc:
                results.append({"request_id": spec.request_id, "status": "failed", "error": str(exc)})
            _progress(**results[-1])
    finally:
        lock.unlink(missing_ok=True)
    done = sum(r["status"] in C.BATCH_COMPLETE for r in results)
    return {"status": "complete" if done == len(plan["requests"]) else "incomplete", "batch_id": plan["batch_id"],
            "completed": done, "requests": len(plan["requests"]), "results": results}


def cmd_ingest(args) -> dict:
    folder = Path(args.batch_dir)
    plan = load_plan(folder)
    item = next((r for r in plan["requests"] if r["request_id"] == args.request_id), None)
    if item is None or plan["lane"] not in C.FILE_LANES:
        raise ContractError("unknown_file_request")
    journal = ingest_provided(spec_from_plan(item), folder, Path(args.file), provided_at_utc=args.provided_at)
    page = journal["pages"][-1]
    return {"status": journal["status"], "request_id": args.request_id, "bytes": page["bytes"],
            "sha256": page["sha256"]}


def cmd_stage(args) -> dict:
    from . import wiring
    from .core.envelope import BatchContext
    from .stage import stage_batch
    folder = Path(args.batch_dir)
    plan = load_plan(folder)
    config = wiring.load_staging_config(plan["t_id"])
    if config.get("raw_only"):
        raise ContractError("raw_only_source")
    doc = wiring.load_mapping_doc(plan["t_id"])
    spatial_meta = None
    if config["reader"]["kind"] == "zip_csv":
        import tempfile
        with tempfile.TemporaryDirectory(prefix="role2-zipcsv-") as work:
            files = wiring.zip_csv_files(folder, plan, config, Path(work))
            header, _ = files[0].read()
            variant, mapping = wiring.pick_variant(doc, header)
            ctx = BatchContext(source_id=plan["source_id"], batch_id=plan["batch_id"],
                               mapping_version=mapping["mapping_version"],
                               record_type=plan["record_type"], staged_at_utc=utc_z())
            summary = stage_batch(folder, ctx=ctx, record_type=plan["record_type"],
                                  mapping_doc=mapping, files=files,
                                  units=wiring.stage_units(wiring.make_normalizer(config)),
                                  scope=wiring.make_scope(config),
                                  code_signature=wiring.code_signature())
    elif config["reader"]["kind"] == "shp_zip":
        import tempfile
        with tempfile.TemporaryDirectory(prefix="role2-shp-") as work:
            files, spatial_meta = wiring.shp_files(folder, plan, config, doc, Path(work))
            mapping_version = doc.get("mapping_version") or doc["mapping"]["mapping_version"]
            variant = "per_file"
            ctx = BatchContext(source_id=plan["source_id"], batch_id=plan["batch_id"],
                               mapping_version=mapping_version,
                               record_type=plan["record_type"], staged_at_utc=utc_z())
            units = wiring.stage_units(wiring.make_normalizer(config, spatial_meta))
            summary = stage_batch(folder, ctx=ctx, record_type=plan["record_type"],
                                  mapping_doc=files[0].mapping_doc, files=files, units=units,
                                  scope=wiring.make_scope(config),
                                  code_signature=wiring.code_signature())
    else:
        files = wiring.xlsx_files(folder, plan, config)
        header, _ = files[0].read()
        variant, mapping = wiring.pick_variant(doc, header)
        ctx = BatchContext(source_id=plan["source_id"], batch_id=plan["batch_id"],
                           mapping_version=mapping["mapping_version"],
                           record_type=plan["record_type"], staged_at_utc=utc_z())
        summary = stage_batch(folder, ctx=ctx, record_type=plan["record_type"],
                              mapping_doc=mapping, files=files,
                              units=wiring.stage_units(wiring.make_normalizer(config)),
                              scope=wiring.make_scope(config),
                              code_signature=wiring.code_signature())
    return {"status": "staged", "variant": variant, "batch_id": summary["batch_id"],
            "resumed": summary["resumed"], "jsonl_lines": summary["jsonl_lines"],
            "sections": summary["sections"]}


def cmd_package(args) -> dict:
    import json as json_module
    from . import wiring
    from .credentials import opened
    from .package_build import build_package
    folder = Path(args.batch_dir)
    plan = load_plan(folder)
    registry = load_registry(args.registry)
    source = check_fetch_gate(registry, plan)
    config = wiring.load_staging_config(plan["t_id"])
    raw_only = bool(config.get("raw_only")) or plan["record_type"] == C.RAW_ONLY
    if raw_only:
        staging = {"sections": [], "jsonl_lines": 0,
                   "staged_at_utc": f"{args.collected[0:4]}-{args.collected[4:6]}-"
                                    f"{args.collected[6:8]}T00:00:00Z"}
        doc = {"mapping": {"mapping_version": "raw-only-v1", "fields": [], "unmapped": []}}
        mapping_version = "raw-only-v1"
        union_fields, union_unmapped = {}, []
    else:
        staging = read_json(folder / "staging.json")
        doc = wiring.load_mapping_doc(plan["t_id"])
        variants = doc.get("variants")
        all_mappings = list(variants.values()) if variants else [doc["mapping"]]
        mapping_version = doc.get("mapping_version") or all_mappings[0]["mapping_version"]
        union_fields, union_unmapped = {}, []
        for m in all_mappings:
            for f in m["fields"]:
                union_fields.setdefault(f["target"], f)
            for header in m["unmapped"]:
                if header not in union_unmapped and header not in {
                        f.get("source") for fm in all_mappings for f in fm["fields"]}:
                    union_unmapped.append(header)
    dataset = wiring.dataset_meta(plan, registry_source=source,
                                  mapping_version=mapping_version,
                                  collected=args.collected, period=args.period,
                                  region=args.region, kind=args.kind,
                                  provider_slug=args.provider)
    schema_inputs = {
        "source_id": plan["source_id"], "record_type": plan["record_type"],
        "mapping_version": mapping_version,
        "columns": [{"name": f["target"], "type": f["type"]} for f in union_fields.values()],
        "source_file": dataset["zip_name"],
        "field_map": {f["target"]: f.get("source") for f in union_fields.values()},
        "unmapped": union_unmapped,
        "extra": {"coordinates": (config.get("coords") or {}).get("evidence"),
                  "missing_markers": "C3 SEMANTIC_TOKENS + placeholder phones",
                  "identifier": "; ".join(f"{f['target']}={f['const']}"
                                          for f in union_fields.values()
                                          if f.get("const") is not None) or None}}
    extra_files = {
        "code/mapping.json": json_module.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8"),
        "code/staging.json": json_module.dumps(config, ensure_ascii=False, indent=2).encode("utf-8"),
        "code/REFERENCE.json": json_module.dumps(
            {"package": "budongi.team_collection", "code_signature": wiring.code_signature(),
             "mapping_t_id": plan["t_id"]}, ensure_ascii=False, indent=2).encode("utf-8")}
    readme = wiring.readme_text(plan, registry_source=source, staging=staging,
                                mapping_version=mapping_version)
    stamp = tuple(int(part) for part in (staging["staged_at_utc"][0:4], staging["staged_at_utc"][5:7],
                                         staging["staged_at_utc"][8:10], staging["staged_at_utc"][11:13],
                                         staging["staged_at_utc"][14:16], staging["staged_at_utc"][17:19]))
    # CRED-001: the user bound each service to an explicit credential ID in the registry;
    # the stored provider metadata is not used for matching (no guessing from metadata).
    with opened(registry["credentials"]) as handles:
        keys = [handle.reveal() for handle in handles.values()]
        report = build_package(folder, Path(args.out), plan=plan, staging=staging,
                               schema_inputs=schema_inputs, dataset=dataset,
                               units=wiring.package_units(), keys=keys, readme=readme,
                               extra_files=extra_files, stamp=stamp)
    return {"status": "packaged", "zip": report["zip"], "sha256": report["sha256"],
            "bytes": report["bytes"], "counts": report["counts"],
            "normalized_withheld": report["normalized_withheld"],
            "parts": bool(report["parts"])}


def cmd_fetch_api(args) -> dict:
    """Keyed lanes B/C/D: paced, journalled, quota-ledgered collection via the supervisor."""
    from datetime import datetime, timezone
    from . import wiring
    from .credentials import opened
    from .issues_net import fetch_issues, find_overlaps
    from .runtime.quota import QuotaLedger
    from .supervisor import LaneSupervisor
    import time
    folder = Path(args.batch_dir)
    registry = load_registry(args.registry)
    plan = load_plan(folder)
    source = check_fetch_gate(registry, plan)
    if plan["lane"] in C.FILE_LANES:
        raise ContractError("not_an_api_lane")
    own = int(plan["record_url"].rsplit("/", 1)[1])
    overlaps = [issue for issue in find_overlaps({"dataset_id": plan["dataset_id"]},
                                                 fetch_issues())
                if issue["number"] != own]
    if overlaps and not args.skip_overlap_check:
        raise ContractError(f"reservation_overlap:{overlaps[0]['number']}")
    specs = [spec_from_plan(item) for item in plan["requests"]]
    origin = specs[0].origin
    credential_ref = specs[0].credential_ref
    units = wiring.lane_units(plan["lane"], registry=registry, origin=origin)
    ledger_dir = folder.parent / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    quota = QuotaLedger(ledger_dir / "runtime.sqlite3",
                        clock=lambda: datetime.now(timezone.utc))
    lock = _lock(folder)
    try:
        with opened({credential_ref: registry["credentials"][credential_ref]}) as handles:
            supervisor = LaneSupervisor(
                units, handle=handles[credential_ref], quota=quota,
                quota_cap=wiring.quota_cap(specs[0].quota_bucket), sleep=time.sleep)
            if args.limit is not None:
                specs = specs[:args.limit]
            results = supervisor.run_batch(specs, folder)
    finally:
        lock.unlink(missing_ok=True)
    rows = [{"request_id": r.request_id, "status": r.status, "pages": r.pages, "rows": r.rows,
             "error": r.error, "blocked_until_utc": r.blocked_until_utc} for r in results]
    done = sum(r.status in C.BATCH_COMPLETE for r in results)
    for row in rows:
        _progress(**row)
    return {"status": "complete" if done == len(plan["requests"]) else "incomplete",
            "batch_id": plan["batch_id"], "completed": done,
            "requests": len(plan["requests"]), "results": rows}


def batch_status(folder: Path) -> dict:
    plan = load_plan(folder)
    rows = []
    for item in plan["requests"]:
        path = folder / "raw" / item["request_id"] / "journal.json"
        if not path.exists():
            rows.append({"request_id": item["request_id"], "status": "not_collected"})
            continue
        journal = read_json(path)
        recover(path.parent, journal)
        try:
            verify(path.parent, journal)
            state = journal["status"]
        except ContractError:
            state = "invalid"
        rows.append({"request_id": item["request_id"], "status": state, "error": journal.get("error")})
    complete = all(r["status"] in C.BATCH_COMPLETE for r in rows)
    return {"batch_id": plan["batch_id"], "t_id": plan["t_id"], "complete": complete, "requests": rows,
            "checked_at_utc": utc_z()}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m budongi.team_collection")
    parser.add_argument("--registry", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--source", required=True)
    p.add_argument("--batch-id", required=True)
    p.add_argument("--record-url", required=True)
    p.add_argument("--data-root", required=True)
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("fetch-files")
    p.add_argument("--batch-dir", required=True)
    p.add_argument("--limit", type=int)
    p = sub.add_parser("ingest-provided")
    p.add_argument("--batch-dir", required=True)
    p.add_argument("--request-id", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--provided-at")
    p = sub.add_parser("status")
    p.add_argument("--batch-dir", required=True)
    p = sub.add_parser("fetch-api")
    p.add_argument("--batch-dir", required=True)
    p.add_argument("--limit", type=int)
    p.add_argument("--skip-overlap-check", action="store_true")
    p = sub.add_parser("stage")
    p.add_argument("--batch-dir", required=True)
    p = sub.add_parser("package")
    p.add_argument("--batch-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--provider", required=True, help="zip name part, no underscores (e.g. KRIC)")
    p.add_argument("--kind", required=True)
    p.add_argument("--region", required=True)
    p.add_argument("--period", required=True)
    p.add_argument("--collected", required=True, help="YYYYMMDD")
    args = parser.parse_args(argv)
    handlers = {"plan": cmd_plan, "fetch-files": cmd_fetch_files, "ingest-provided": cmd_ingest,
                "status": lambda a: batch_status(Path(a.batch_dir)),
                "fetch-api": cmd_fetch_api, "stage": cmd_stage, "package": cmd_package}
    try:
        result = handlers[args.command](args)
    except ContractError as exc:
        print(json.dumps({"status": "contract_error", "error": str(exc)}), flush=True)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    incomplete = result.get("status") == "incomplete" or result.get("complete") is False
    return 3 if incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main())

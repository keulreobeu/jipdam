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
    args = parser.parse_args(argv)
    handlers = {"plan": cmd_plan, "fetch-files": cmd_fetch_files, "ingest-provided": cmd_ingest,
                "status": lambda a: batch_status(Path(a.batch_dir))}
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

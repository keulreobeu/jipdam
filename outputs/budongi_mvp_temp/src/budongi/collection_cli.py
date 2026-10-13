"""Collection CLI is separate from the historical serving commands."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

from .collection import CollectionError, SERVICES, collection_status, create_plan, fetch_collection
from .collection_db import build_databases, pack_collection


def add_collection_parser(subparsers) -> None:
    parser = subparsers.add_parser("collection", help="Archive MOLIT XML and build offline observation DBs")
    actions = parser.add_subparsers(dest="collection_action", required=True)
    plan = actions.add_parser("plan", help="Create fixed Seoul service/district/month scope; no key or network")
    plan.add_argument("--batch-id", required=True)
    plan.add_argument("--snapshot-date", default=date.today().isoformat())
    plan.add_argument("--districts", nargs="+")
    plan.add_argument("--months", nargs="+")
    plan.add_argument("--services", nargs="+", choices=list(SERVICES))
    plan.add_argument("--per-page", type=int, default=1000)
    plan.add_argument("--record-url", default="")
    fetch = actions.add_parser("fetch", help="Verify/reuse complete XML; retrieve only missing pages")
    fetch.add_argument("--credential", action="append", default=[], metavar="SERVICE=ID")
    fetch.add_argument("--credentials-file", type=Path, help="JSON service-to-opaque-ID map, never raw keys")
    fetch.add_argument("--cache-dir", action="append", type=Path, default=[])
    fetch.add_argument("--limit", type=int, help="Maximum new region/month queries; useful for pilot verification")
    fetch.add_argument("--interval", type=float, default=1)
    actions.add_parser("status", help="Read/verify archive counts, failures and missing query scope")
    build = actions.add_parser("build-db", help="Build separate rental/sale DBs from XML; no key or network")
    build.add_argument("--output", type=Path)
    build.add_argument("--allow-partial", action="store_true")
    canonical = actions.add_parser("integrate", help="Build provenance/regions/entities/candidate joins offline")
    canonical.add_argument("--db-directory", type=Path)
    canonical.add_argument("--output", type=Path)
    canonical.add_argument("--previous", type=Path, help="Read a previous sealed canonical snapshot; publish to a new output")
    canonical.add_argument("--allow-partial", action="store_true")
    file_stage = actions.add_parser("stage-file", help="Preserve and validate a registry-approved CSV/JSON/XLSX locally")
    file_stage.add_argument("--registry", required=True, type=Path)
    file_stage.add_argument("--source-id", required=True)
    file_stage.add_argument("--input", required=True, type=Path)
    file_stage.add_argument("--output", required=True, type=Path)
    file_integrate = actions.add_parser("integrate-file", help="Publish a validated file stage to a new canonical snapshot")
    file_integrate.add_argument("--directory", required=True, type=Path)
    file_integrate.add_argument("--registry", required=True, type=Path)
    file_integrate.add_argument("--output", required=True, type=Path)
    file_integrate.add_argument("--batch-id", required=True)
    file_integrate.add_argument("--snapshot-date", required=True)
    file_integrate.add_argument("--observation-from", required=True)
    file_integrate.add_argument("--record-url", required=True)
    file_integrate.add_argument("--previous", type=Path)
    pack = actions.add_parser("pack", help="Package XML, manifests, DBs, summary; no Drive upload")
    pack.add_argument("--output", required=True, type=Path)
    pack.add_argument("--db-directory", type=Path)
    pack.add_argument("--allow-partial", action="store_true")
    for command in (plan, fetch, build, canonical, pack):
        command.add_argument("--directory", type=Path, required=True)
    actions.choices["status"].add_argument("--directory", type=Path, required=True)


def run_collection(args) -> None:
    root = getattr(args, "directory", None)
    try:
        if args.collection_action == "stage-file":
            from .source_files import stage_file
            result = stage_file(registry_path=args.registry, source_id=args.source_id, input_path=args.input, output=args.output)
        elif args.collection_action == "integrate-file":
            from .collection_integrate import integrate_file
            result = integrate_file(root, args.registry, args.output, batch_id=args.batch_id,
                                    snapshot_date=args.snapshot_date, observation_from=args.observation_from,
                                    record_url=args.record_url, previous=args.previous)
        elif args.collection_action == "plan":
            result = create_plan(root, batch_id=args.batch_id, snapshot_date=args.snapshot_date,
                                 districts=args.districts, services=args.services, months=args.months,
                                 per_page=args.per_page, record_url=args.record_url)
            result = result | {"status": collection_status(root)}
        elif args.collection_action == "status":
            result = collection_status(root)
        elif args.collection_action == "fetch":
            credentials = {}
            if args.credentials_file:
                try:
                    credentials = json.loads(args.credentials_file.read_text(encoding="utf-8-sig"))
                except (OSError, UnicodeError, ValueError):
                    raise CollectionError("invalid_credentials_id_file") from None
                if not isinstance(credentials, dict):
                    raise CollectionError("invalid_credentials_id_file")
            for value in args.credential:
                if "=" not in value:
                    raise CollectionError("credential_format_service_equals_id")
                service, identifier = value.split("=", 1)
                credentials[service] = identifier
            import re
            if any(s not in SERVICES or not isinstance(identifier, str) or
                   not re.fullmatch(r"[0-9a-fA-F-]{36}", identifier) for s, identifier in credentials.items()):
                raise CollectionError("invalid_opaque_credential_id")
            def progress(value):
                print(json.dumps(value, ensure_ascii=False), file=sys.stderr, flush=True)
            result = fetch_collection(root, credentials, interval=args.interval, limit=args.limit,
                                      cache_dirs=args.cache_dir, progress=progress)
        elif args.collection_action == "build-db":
            result = build_databases(root, args.output or root / "db", allow_partial=args.allow_partial)
        elif args.collection_action == "integrate":
            from .collection_integrate import integrate_collection
            result = integrate_collection(root, args.db_directory or root / "db", args.output or root / "canonical",
                                          previous=args.previous, allow_partial=args.allow_partial)
        else:
            result = pack_collection(root, args.output, db_directory=args.db_directory or root / "db",
                                     allow_partial=args.allow_partial)
    except CollectionError as exc:
        print(json.dumps({"status": "collection_error", "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(2) from None
    except (OSError, sqlite3.Error, TypeError, KeyError, ValueError):
        print(json.dumps({"status": "collection_error", "error": "collection_processing_failed"}))
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.collection_action == "fetch" and not result["complete"]:
        raise SystemExit(3)
    if args.collection_action == "stage-file" and (not result["complete"] or result["counts"]["rejected"]):
        raise SystemExit(3)

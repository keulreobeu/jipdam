"""CLI adapters for the offline statistics store."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .statistics_storage import StatisticsError, import_statistics, statistics_status


def add_statistics_parser(sub) -> None:
    parser = sub.add_parser("statistics", help="Preserve provided statistics XLSX in a separate offline database")
    actions = parser.add_subparsers(dest="statistics_action", required=True)
    importer = actions.add_parser("import")
    importer.add_argument("--statistics-db", type=Path, required=True)
    importer.add_argument("--batch-id", required=True)
    inputs = importer.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--files", type=Path, nargs="+")
    inputs.add_argument("--input-list", type=Path, help="UTF-8 JSON array of explicit XLSX paths")
    status = actions.add_parser("status")
    status.add_argument("--statistics-db", type=Path, required=True)
    audit = actions.add_parser("audit")
    audit.add_argument("--statistics-db", type=Path, required=True)
    audit.add_argument("--input-list", type=Path)
    audit.add_argument("--record-reviews", action="store_true", help="Append duplicate/base evidence without changing source cells")


def run_statistics(args) -> None:
    try:
        if args.statistics_action == "status":
            result = statistics_status(args.statistics_db)
        elif args.statistics_action == "audit":
            from .statistics_audit import audit_statistics, record_audit_reviews
            originals = None
            if args.input_list:
                paths = json.loads(args.input_list.read_text(encoding="utf-8-sig"))
                if not isinstance(paths, list) or any(not isinstance(p,str) for p in paths):
                    raise StatisticsError("Input list must be a JSON array of paths")
                originals = [Path(p) for p in paths]
            result = audit_statistics(args.statistics_db, originals)
            if args.record_reviews:
                result["recorded_reviews"] = record_audit_reviews(args.statistics_db, result)
        else:
            files = args.files
            if args.input_list:
                paths = json.loads(args.input_list.read_text(encoding="utf-8-sig"))
                if not isinstance(paths, list) or not paths or any(not isinstance(p, str) for p in paths):
                    raise StatisticsError("Input list must be a nonempty JSON array of paths")
                files = [Path(p) for p in paths]
            result = import_statistics(args.statistics_db, args.batch_id, files)
    except (StatisticsError, ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"status": "statistics_error", "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(2) from None
    print(json.dumps(result, ensure_ascii=False, indent=2))

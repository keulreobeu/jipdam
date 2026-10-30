"""CLI boundary with safe JSON errors and explicit offline commands."""
from __future__ import annotations

import json
from pathlib import Path

from . import VERSION
from .common import ExecutionFailure, PipelineError, checked_path, load_json


def add_parser(sub):
    parser = sub.add_parser("pipeline", help="Offline metadata catalog, ETL, lineage and benchmarks")
    parser.add_argument("--root", type=Path, default=Path("data/pipeline"))
    commands = parser.add_subparsers(dest="pipeline_command", required=True)
    catalog = commands.add_parser("catalog")
    catalog_sub = catalog.add_subparsers(dest="catalog_command", required=True)
    imp = catalog_sub.add_parser("import")
    imp.add_argument("--workbook", type=Path, required=True)
    imp.add_argument("--namespace", required=True)
    inventory = commands.add_parser("inventory")
    inventory.add_argument("--request", type=Path)
    for command in ["plan", "run", "benchmark"]:
        p = commands.add_parser(command)
        p.add_argument("--request", type=Path, required=True)
        if command == "benchmark":
            p.add_argument("--repetitions", type=int, default=5)
            p.add_argument("--candidate-engine", choices=["python", "pandas_full", "pandas_chunked", "duckdb"])
    status = commands.add_parser("status")
    status.add_argument("--run-id")
    lineage = commands.add_parser("lineage")
    lineage.add_argument("--run-id", required=True)
    lineage.add_argument("--record-id", required=True)
    report = commands.add_parser("report")
    selection = report.add_mutually_exclusive_group()
    selection.add_argument("--request", type=Path, help="Evaluate explicit approved targets against saved baseline/candidate runs")
    selection.add_argument("--assessment-id", help="Explicitly select a saved target assessment")


def run_cli(args):
    from .benchmark import assess_targets, benchmark, performance_report
    from .catalog import import_workbook, inventory_status, register_inventory
    from .runner import lineage, plan_request, run_pipeline, status
    code = 0
    try:
        root = checked_path(args.root)
        command = args.pipeline_command
        if command == "catalog":
            result = import_workbook(root, args.workbook, args.namespace)
        elif command == "inventory":
            result = register_inventory(root, load_json(args.request)) if args.request else inventory_status(root)
        elif command == "plan":
            plan = plan_request(root, load_json(args.request))
            result = {k: v for k, v in plan.items() if k not in {"sources", "dataset"}}
        elif command == "run":
            # Invalid/precondition requests exit 2. A started execution failure exits 1.
            request = load_json(args.request)
            plan_request(root, request)
            try:
                result = run_pipeline(root, request)
            except ExecutionFailure as exc:
                result, code = {"status": "failed", "error_code": str(exc)}, 1
        elif command == "benchmark":
            result = benchmark(root, load_json(args.request), repetitions=args.repetitions, candidate_engine=args.candidate_engine)
            if result["status"] == "incomparable":
                code = 2
        elif command == "status":
            result = {"runs": status(root, args.run_id)}
        elif command == "lineage":
            result = {"lineage": lineage(root, args.run_id, args.record_id)}
        else:
            result = assess_targets(root, load_json(args.request)) if args.request else performance_report(root, args.assessment_id)
            if result.get("targets_status") == "not_met":
                code = 2
    except ExecutionFailure as exc:
        result, code = {"status": "failed", "error_code": str(exc)}, 1
    except PipelineError as exc:
        result, code = {"status": "blocked", "error_code": str(exc)}, 2
    except (KeyError, TypeError, ValueError):
        result, code = {"status": "blocked", "error_code": "invalid_pipeline_contract"}, 2
    except Exception:
        result, code = {"status": "failed", "error_code": "pipeline_io_or_dependency_error"}, 1
    print(json.dumps({"schema_version": VERSION, **result}, ensure_ascii=False, indent=2))
    if code:
        raise SystemExit(code)

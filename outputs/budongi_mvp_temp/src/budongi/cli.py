"""Command line entry points for the temporary project."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .agent import ask
from .eval import evaluate
from .storage import connect, import_snapshot, inspect_legacy
from .tools import execute_tool


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jipdam")
    parser.add_argument("--db", type=Path, default=Path("data/historical/serving.sqlite3"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db", help="Create empty serving schema")
    doctor = sub.add_parser("doctor", help="Report available snapshots and row counts")
    doctor.add_argument("--snapshot-id")
    legacy = sub.add_parser("inspect-legacy", help="Inspect old flat CSV without importing supply price as trades")
    legacy.add_argument("csv", type=Path)
    importer = sub.add_parser("import-snapshot", help="Import normalized 2023 historical CSVs")
    importer.add_argument("--snapshot-id", required=True)
    importer.add_argument("--snapshot-date", required=True)
    importer.add_argument("--apartments", required=True, type=Path)
    importer.add_argument("--transactions", required=True, type=Path)
    tool = sub.add_parser("tool", help="Run one validated data tool without a model")
    tool.add_argument("--snapshot-id", required=True)
    tool.add_argument("--name", required=True)
    tool.add_argument("--arguments", default="{}")
    chat = sub.add_parser("ask", help="Ask a local OpenAI-compatible 4B model")
    chat.add_argument("--snapshot-id", required=True)
    chat.add_argument("--question", required=True)
    chat.add_argument("--model", required=True)
    chat.add_argument("--endpoint", default=os.environ.get("OLLAMA_ENDPOINT", "http://127.0.0.1:11434/v1/chat/completions"))
    chat.add_argument("--run-id", default=None)
    chat.add_argument("--output-dir", type=Path, default=Path("."))
    batch = sub.add_parser("run-eval", help="Run all Golden questions and write stagewise report")
    batch.add_argument("--snapshot-id", required=True)
    batch.add_argument("--golden", type=Path, required=True)
    batch.add_argument("--model", required=True)
    batch.add_argument("--endpoint", default=os.environ.get("OLLAMA_ENDPOINT", "http://127.0.0.1:11434/v1/chat/completions"))
    batch.add_argument("--run-id", required=True)
    batch.add_argument("--output-dir", type=Path, default=Path("."))
    score = sub.add_parser("evaluate", help="Score an existing prediction JSONL")
    score.add_argument("--golden", type=Path, required=True)
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--report", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "inspect-legacy":
        _print(inspect_legacy(args.csv))
        return
    if args.command == "evaluate":
        _print(evaluate(args.golden, args.predictions, args.report))
        return
    connection = connect(args.db)
    try:
        if args.command == "init-db":
            _print({"database": str(args.db), "status": "schema_ready"})
        elif args.command == "doctor":
            snapshots = [dict(row) for row in connection.execute("SELECT snapshot_id, snapshot_date, source_manifest FROM snapshots ORDER BY snapshot_id")]
            counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                      for table in ("apartments", "transactions", "locations", "facilities")}
            sources = {row[0] for table in ("apartments", "transactions")
                       for row in connection.execute(f"SELECT DISTINCT source FROM {table}")}
            contains_synthetic = any(source.startswith("synthetic_") for source in sources)
            synthetic_only = bool(sources) and all(source.startswith("synthetic_") for source in sources)
            _print({"database": str(args.db), "snapshots": snapshots, "row_counts": counts,
                    "synthetic_only": synthetic_only, "contains_synthetic": contains_synthetic,
                    "ready_for_real_eval": bool(snapshots and counts["apartments"] and counts["transactions"]
                                                and not contains_synthetic)})
        elif args.command == "import-snapshot":
            _print(import_snapshot(connection, snapshot_id=args.snapshot_id,
                                   snapshot_date=args.snapshot_date, apartments_csv=args.apartments,
                                   transactions_csv=args.transactions))
        elif args.command == "tool":
            _print(execute_tool(connection, args.snapshot_id, args.name, json.loads(args.arguments)))
        elif args.command == "ask":
            run_id = args.run_id or datetime.now(timezone.utc).strftime("manual_%Y%m%d_%H%M%S")
            _print(ask(connection, snapshot_id=args.snapshot_id, question=args.question,
                       model=args.model, endpoint=args.endpoint, run_id=run_id,
                       output_dir=args.output_dir))
        elif args.command == "run-eval":
            run_path = args.output_dir / "runs" / f"{args.run_id}.jsonl"
            if run_path.exists():
                raise ValueError(f"Run already exists: {run_path}")
            with args.golden.open("r", encoding="utf-8") as stream:
                golden = [json.loads(line) for line in stream if line.strip()]
            if len({item["id"] for item in golden}) != len(golden):
                raise ValueError("Golden IDs must be unique")
            manifest = {"run_id": args.run_id, "created_at": datetime.now(timezone.utc).isoformat(),
                        "model_version": args.model, "snapshot_id": args.snapshot_id,
                        "golden_path": str(args.golden), "eval_version": "deterministic_v1",
                        "note": "Generation fact extraction is not yet implemented."}
            run_path.parent.mkdir(parents=True, exist_ok=True)
            (run_path.parent / f"{args.run_id}.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            for item in golden:
                ask(connection, snapshot_id=args.snapshot_id, question=item["question"],
                    question_id=item["id"], model=args.model, endpoint=args.endpoint,
                    run_id=args.run_id, output_dir=args.output_dir)
            report = args.output_dir / "reports" / f"{args.run_id}.csv"
            _print(evaluate(args.golden, run_path, report))
    finally:
        connection.close()


if __name__ == "__main__":
    main()

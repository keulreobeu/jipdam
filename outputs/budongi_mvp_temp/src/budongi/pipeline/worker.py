"""Private worker entry point: no shell, network, provider, or plugin dispatch."""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from .adapters import execute_adapter
from .common import PipelineError, atomic_json, load_json, writer_lock


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    args = parser.parse_args()
    job = load_json(args.job)
    import psutil
    work = Path(job["directory"]).parent
    with writer_lock(work):
        if (work / "launch-cancelled.json").exists():
            return
        atomic_json(work / "worker-state.json", {"pid": os.getpid(), "create_time": psutil.Process().create_time()})
        execute(job)


def execute(job):
    started = time.perf_counter_ns()
    try:
        result = execute_adapter(job["dataset"], job["sources"], Path(job["directory"]),
                                 engine=job["engine"], max_input_rows=job.get("max_input_rows"))
        result.update(status="success", adapter_duration_ms=(time.perf_counter_ns() - started) / 1_000_000)
        atomic_json(Path(job["directory"]) / "worker-result.json", result)
    except Exception as exc:
        code = str(exc) if isinstance(exc, PipelineError) else "adapter_validation_or_io_failed"
        atomic_json(Path(job["directory"]) / "worker-result.json", {"status": "failed", "error_code": code,
                    "evidence": exc.evidence if isinstance(exc, PipelineError) else None,
                    "adapter_duration_ms": (time.perf_counter_ns() - started) / 1_000_000})
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()

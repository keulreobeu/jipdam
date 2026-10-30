"""Single-writer coordinator: verify -> isolated work -> verify -> publish -> index."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

from .adapters import ADAPTERS
from .catalog import Catalog
from .common import (ExecutionFailure, PipelineError, atomic_json, checked_path, dumps, identifier, load_json,
                     now, sha_file, signature, writer_lock)
from .metrics import code_version, environment, observe


def plan_request(root, request):
    if not isinstance(request, dict):
        raise PipelineError("request_object_required")
    allowed = {"dataset_id", "adapter_id", "batch_id", "mapping_version", "input_refs", "output_root", "engine", "max_input_rows", "timeout_seconds"}
    if set(request) - allowed:
        raise PipelineError("unknown_request_field")
    did, batch, version = [identifier(request[k]) for k in ["dataset_id", "batch_id", "mapping_version"]]
    if checked_path(request["output_root"]) != checked_path(root):
        raise PipelineError("output_root_must_equal_catalog_root")
    refs = request["input_refs"]
    if not isinstance(refs, list) or not refs or any(not isinstance(v, str) for v in refs) or len(refs) != len(set(refs)):
        raise PipelineError("distinct_registered_input_refs_required")
    engine = request.get("engine", "python")
    if engine not in {"python", "pandas_full", "pandas_chunked", "duckdb"}:
        raise PipelineError("unregistered_engine")
    limit = request.get("max_input_rows")
    timeout = request.get("timeout_seconds", 3600)
    if limit is not None and (type(limit) is not int or limit < 1):
        raise PipelineError("invalid_sample_limit")
    if type(timeout) is not int or not 1 <= timeout <= 86400:
        raise PipelineError("invalid_timeout")
    with Catalog(root, readonly=True) as catalog:
        row = catalog.db.execute("SELECT * FROM datasets WHERE dataset_id=? AND mapping_version=?", (did, version)).fetchone()
        if not row or row["adapter_id"] not in ADAPTERS or row["adapter_id"] != request["adapter_id"]:
            raise PipelineError("unregistered_dataset_or_adapter")
        dataset = dict(row)
        dataset["contract"] = json.loads(dataset.pop("contract_json"))
        sources = []
        for ref in sorted(refs):
            source = catalog.db.execute("SELECT i.*,l.path FROM inputs i JOIN artifact_locations l USING(location_id) WHERE input_id=?", (ref,)).fetchone()
            if not source or source["dataset_id"] != did or source["mapping_version"] != version:
                raise PipelineError("input_not_registered_for_dataset")
            source = dict(source)
            source["descriptor"] = json.loads(source.pop("descriptor_json"))
            path = checked_path(source["path"])
            if not path.is_file() or sha_file(path) != source["sha256"]:
                raise PipelineError("input_missing_or_tampered")
            source["path"] = str(path)
            sources.append(source)
    content = [{"sha256": s["sha256"], "input_id": s["input_id"], "descriptor": s["descriptor"]} for s in sources]
    if len({(s["sha256"], s["descriptor"].get("source_ref", s["input_id"])) for s in sources}) != len(sources):
        raise PipelineError("duplicate_logical_input")
    implementation = {p.name: sha_file(p) for p in Path(__file__).parent.glob("*.py")}
    for name in ["collection.py", "collection_db.py", "statistics_storage.py", "statistics_sources.json"]:
        implementation[name] = sha_file(Path(__file__).parent.parent / name)
    logical = signature([did, version, dataset["contract"], content, limit])
    return {"status": "ready", "dataset": dataset, "sources": sources, "batch_id": batch,
            "semantic_signature": logical, "input_signature": signature([logical, engine, implementation]),
            "implementation_signature": signature(implementation), "engine": engine, "max_input_rows": limit,
            "timeout_seconds": timeout, "input_bytes": sum(Path(s["path"]).stat().st_size for s in sources)}


def verify_result(root, result, receipt_sha=None):
    identifier(result["run_id"])
    if not {"data.parquet", "quarantine.jsonl", "worker-result.json"}.issubset(result.get("files", {})):
        raise PipelineError("incomplete_output_receipt")
    directory = checked_path(Path(root) / "outputs" / result["run_id"])
    receipt = directory / "run.json"
    if not receipt.is_file() or (receipt_sha is not None and sha_file(receipt) != receipt_sha):
        raise PipelineError("output_receipt_missing_or_tampered")
    for name, expected in result["files"].items():
        if Path(name).name != name:
            raise PipelineError("invalid_output_reference")
        path = checked_path(directory / name)
        if not path.is_file() or sha_file(path) != expected:
            raise PipelineError("output_missing_or_tampered")
    return directory


def settle_running(catalog):
    recovered = set()
    for old in list(catalog.db.execute("SELECT * FROM runs WHERE status='running'")):
        work = checked_path(catalog.root / "work" / old["run_id"])
        # Coordinator death does not kill its worker. Both lifetime lock and PID identity
        # must settle before any replacement attempt may run.
        if work.exists():
            try:
                with writer_lock(work):
                    marker = work / "worker-state.json"
                    if marker.exists():
                        import psutil
                        identity = load_json(marker)
                        try:
                            child = psutil.Process(identity["pid"])
                            if abs(child.create_time() - identity["create_time"]) < 0.01:
                                raise PipelineError("interrupted_worker_still_active")
                        except psutil.NoSuchProcess:
                            pass
                    elif (work / "job.json").exists():
                        if load_json(work / "job.json").get("worker_protocol") != 1:
                            raise PipelineError("interrupted_worker_launch_uncertain")
                        # Lock excludes an executing worker; a delayed worker must see this
                        # cancellation before starting. This closes the pre-Popen crash window.
                        atomic_json(work / "launch-cancelled.json", {"run_id": old["run_id"], "at": now()})
            except PipelineError as exc:
                if str(exc) == "catalog_writer_busy":
                    raise PipelineError("interrupted_worker_still_active") from None
                raise
        receipt = catalog.root / "outputs" / old["run_id"] / "run.json"
        if receipt.is_file():
            if not old["receipt_sha256"]:
                raise PipelineError("prepared_receipt_anchor_missing")
            result = load_json(receipt)
            if result.get("input_signature") != old["input_signature"] or result.get("status") != "success" or result.get("run_id") != old["run_id"]:
                raise PipelineError("interrupted_publication_conflict")
            verify_result(catalog.root, result, old["receipt_sha256"])
            with catalog.db:
                catalog.db.execute("UPDATE runs SET status='success',finished_at=?,result_json=?,receipt_sha256=? WHERE run_id=?", (now(), dumps(result), sha_file(receipt), old["run_id"]))
            recovered.add(old["run_id"])
            continue
        atomic_json(catalog.root / "events" / (old["run_id"] + "-interrupted.json"), {"run_id": old["run_id"], "status": "interrupted", "at": now()})
        with catalog.db:
            catalog.db.execute("UPDATE runs SET status='interrupted',finished_at=? WHERE run_id=?", (now(), old["run_id"]))
    return recovered


def run_pipeline(root, request):
    start = time.perf_counter_ns()
    with writer_lock(root), Catalog(root) as catalog:
        for name in ["work", "outputs", "events", "benchmarks"]:
            checked_path(catalog.root / name)
        plan = plan_request(root, request)
        recovered = settle_running(catalog)
        did, batch, version = plan["dataset"]["dataset_id"], plan["batch_id"], plan["dataset"]["mapping_version"]
        previous = list(catalog.db.execute("SELECT * FROM runs WHERE dataset_id=? AND batch_id=? AND mapping_version=? ORDER BY attempt", (did, batch, version)))
        for old in previous:
            if old["input_signature"] != plan["input_signature"]:
                raise PipelineError("batch_input_changed_use_new_batch")
            if old["status"] == "success":
                result = json.loads(old["result_json"])
                verify_result(root, result, old["receipt_sha256"])
                return result | {"reused": True, "recovered": old["run_id"] in recovered}
        run_id = uuid.uuid4().hex
        attempt = len(previous) + 1
        started = now()
        work = checked_path(catalog.root / "work" / run_id)
        work.mkdir(parents=True)
        with catalog.db:
            catalog.db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?)", (run_id, did, batch, version, plan["input_signature"], attempt, "running", started, None, None, None))
        atomic_json(catalog.root / "events" / (run_id + "-started.json"), {"run_id": run_id, "status": "running", "at": started, "attempt": attempt})
        process = None
        memory, worker = None, None
        try:
            copied = []
            copy_start = time.perf_counter_ns()
            for index, source in enumerate(plan["sources"]):
                original = Path(source["path"])
                target = checked_path(work / "inputs" / str(index) / original.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, target)
                if sha_file(target) != source["sha256"]:
                    raise PipelineError("source_changed_during_copy")
                copied.append(source | {"path": str(target)})
            copy_ms = (time.perf_counter_ns() - copy_start) / 1_000_000
            artifacts = checked_path(work / "artifacts")
            artifacts.mkdir()
            job = work / "job.json"
            atomic_json(job, {"worker_protocol": 1, "dataset": plan["dataset"], "sources": copied, "directory": str(artifacts), "engine": plan["engine"], "max_input_rows": plan["max_input_rows"]})
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            worker_start = time.perf_counter_ns()
            process = subprocess.Popen([sys.executable, "-X", "utf8", "-m", "budongi.pipeline.worker", "--job", str(job)],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
            memory = observe(process, timeout=plan["timeout_seconds"])
            worker_ms = (time.perf_counter_ns() - worker_start) / 1_000_000
            worker = load_json(artifacts / "worker-result.json") if (artifacts / "worker-result.json").exists() else {}
            if memory["timed_out"] or process.returncode != 0 or worker.get("status") != "success":
                raise PipelineError("worker_timeout" if memory["timed_out"] else worker.get("error_code", "worker_interrupted"))
            files = {p.name: sha_file(p) for p in artifacts.iterdir() if p.is_file()}
            result = worker | {"schema_version": "jipdam_pipeline_v1", "run_id": run_id, "dataset_id": did, "batch_id": batch,
                "mapping_version": version, "input_signature": plan["input_signature"], "semantic_signature": plan["semantic_signature"],
                "implementation_signature": plan["implementation_signature"], "attempt": attempt, "engine": plan["engine"],
                "max_input_rows": plan["max_input_rows"], "started_at_utc": started, "finished_at_utc": now(),
                "duration_ms": worker_ms, "end_to_end_duration_ms": (time.perf_counter_ns() - start) / 1_000_000,
                "stages": {"input_snapshot_ms": copy_ms, "worker_ms": worker_ms, "normalize_validate_write_ms": worker["adapter_duration_ms"]},
                "memory": memory, "input_bytes": plan["input_bytes"], "output_bytes": sum(p.stat().st_size for p in artifacts.iterdir()),
                "environment": environment(), "code": code_version(), "files": files, "reused": False,
                "throughput_input_rows_per_second": worker["counts"]["input_rows"] / (worker_ms / 1000) if worker_ms else None}
            atomic_json(artifacts / "run.json", result)
            receipt_sha = sha_file(artifacts / "run.json")
            # Anchor the completed receipt before its directory becomes visible.
            with catalog.db:
                catalog.db.execute("UPDATE runs SET receipt_sha256=? WHERE run_id=? AND status='running'", (receipt_sha, run_id))
            destination = checked_path(catalog.root / "outputs" / run_id)
            destination.parent.mkdir(exist_ok=True)
            # A UUID is new; never replace a published directory (also on POSIX).
            if destination.exists():
                raise PipelineError("output_already_exists")
            os.rename(artifacts, destination)
            with catalog.db:
                catalog.db.execute("UPDATE runs SET status='success',finished_at=?,result_json=?,receipt_sha256=? WHERE run_id=?", (now(), dumps(result), receipt_sha, run_id))
            return result
        except BaseException as exc:
            if process is not None and process.poll() is None:
                import psutil
                try:
                    parent = psutil.Process(process.pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()
                    process.wait(timeout=10)
                except (psutil.Error, OSError, subprocess.TimeoutExpired):
                    pass
            # A receipt published before an index failure is recovered, never rerun.
            if not (catalog.root / "outputs" / run_id / "run.json").exists():
                code = str(exc) if isinstance(exc, PipelineError) else "pipeline_execution_failed"
                failure = {"schema_version": "jipdam_pipeline_v1", "run_id": run_id, "status": "failed", "error_code": code,
                           "memory": memory, "worker_evidence": worker,
                           "at": now(), "duration_ms": (time.perf_counter_ns() - start) / 1_000_000}
                atomic_json(catalog.root / "events" / (run_id + "-failed.json"), failure)
                with catalog.db:
                    catalog.db.execute("UPDATE runs SET status='failed',finished_at=?,result_json=? WHERE run_id=?", (now(), dumps(failure), run_id))
            raise ExecutionFailure(str(exc) if isinstance(exc, PipelineError) else "pipeline_execution_failed") from None


def status(root, run_id=None):
    with Catalog(root, readonly=True) as catalog:
        query = "SELECT run_id,dataset_id,batch_id,attempt,status,started_at,finished_at FROM runs"
        return [dict(r) for r in catalog.db.execute(query + (" WHERE run_id=?" if run_id else " ORDER BY started_at DESC LIMIT 100"), (run_id,) if run_id else ())]


def lineage(root, run_id, record_id):
    import duckdb
    identifier(run_id)
    with Catalog(root, readonly=True) as catalog:
        row = catalog.db.execute("SELECT * FROM runs WHERE run_id=? AND status='success'", (run_id,)).fetchone()
        if not row:
            raise PipelineError("successful_run_required")
        result = json.loads(row["result_json"])
        directory = verify_result(root, result, row["receipt_sha256"])
    with duckdb.connect(config={"threads": 1}) as db:
        rows = db.execute("SELECT input_id,source_sha256,source_ref,section,source_row,source_column FROM read_parquet(?) WHERE record_id=?", [str(directory / "data.parquet"), record_id]).fetchall()
    return [dict(zip(["input_id", "source_sha256", "source_ref", "section", "source_row", "source_column"], r)) for r in rows]

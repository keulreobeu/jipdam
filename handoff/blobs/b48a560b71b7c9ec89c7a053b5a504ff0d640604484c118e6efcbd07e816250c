"""Repeated isolated runs and explicit comparability; no invented improvement target."""
from __future__ import annotations

import math
import re
import statistics
import uuid

from .common import PipelineError, atomic_json, checked_path, identifier, load_json, now, sha_file, signature, writer_lock
from .catalog import Catalog
from .runner import run_pipeline, verify_result


def summarize(runs):
    values = sorted(r["duration_ms"] for r in runs)
    memory = [r["memory"]["peak_rss_bytes"] for r in runs]
    return {"repetitions": len(values), "median_duration_ms": statistics.median(values),
            "p95_duration_ms": values[max(0, math.ceil(len(values) * .95) - 1)],
            "p95_method": "nearest_rank; exploratory with small samples", "durations_ms": values,
            "max_peak_rss_bytes": max(memory) if all(v is not None for v in memory) else None,
            "run_ids": [r["run_id"] for r in runs]}


def compare(baseline, candidate):
    all_runs = baseline + candidate
    comparable = (len(baseline) >= 5 and len(candidate) >= 5 and
                  len({r["semantic_signature"] for r in all_runs}) == 1 and
                  len({r["result_digest"] for r in all_runs}) == 1 and
                  len({signature(r["counts"]) for r in all_runs}) == 1 and
                  len({signature(r["environment"]) for r in all_runs}) == 1)
    result = {"status": "comparable" if comparable else "incomparable", "baseline": summarize(baseline), "candidate": summarize(candidate)}
    if comparable:
        before, after = result["baseline"]["median_duration_ms"], result["candidate"]["median_duration_ms"]
        result["duration_improvement_percent"] = (before - after) / before * 100 if before > 0 else None
    return result


def benchmark(root, request, *, repetitions=5, candidate_engine=None):
    if type(repetitions) is not int or not 5 <= repetitions <= 100:
        raise PipelineError("benchmark_requires_5_to_100_repetitions")
    if candidate_engine is not None and candidate_engine == request.get("engine", "python"):
        raise PipelineError("candidate_must_differ")
    bid = uuid.uuid4().hex
    baseline, candidate = [], []
    for index in range(repetitions):
        baseline.append(run_pipeline(root, request | {"batch_id": f"bench-{bid}-base-{index}"}))
        if candidate_engine:
            candidate.append(run_pipeline(root, request | {"batch_id": f"bench-{bid}-candidate-{index}", "engine": candidate_engine}))
    stable = len({(r["semantic_signature"], r["result_digest"]) for r in baseline}) == 1
    report = {"schema_version": "jipdam_benchmark_v1", "benchmark_id": bid, "dataset_id": request["dataset_id"],
              "created_at": now(), "status": "baseline_recorded" if stable else "incomparable", "baseline": summarize(baseline),
              "baseline_kind": "current_instrumented_adapter; not an historical timing claim",
              "coverage": baseline[0]["coverage"], "max_input_rows": request.get("max_input_rows"),
              "source_signature": baseline[0]["semantic_signature"], "result_digest": baseline[0]["result_digest"],
              "targets_status": "pending_user_targets", "m1_complete": False,
              "cache_policy": "fresh worker/output per run; OS filesystem cache uncontrolled"}
    if candidate:
        report["comparison"] = compare(baseline, candidate)
        report["status"] = report["comparison"]["status"]
    atomic_json(root / "benchmarks" / (bid + ".json"), report)
    return report


def recorded_runs(root, benchmark_id):
    """Read actual anchored successful runs, not editable summary statistics."""
    item = load_json(root / "benchmarks" / (identifier(benchmark_id) + ".json"))
    ids = item["baseline"]["run_ids"]
    if item["benchmark_id"] != benchmark_id or len(ids) < 5 or len(ids) != len(set(ids)):
        raise PipelineError("invalid_benchmark_run_set")
    runs = []
    with Catalog(root, readonly=True) as catalog:
        for rid in ids:
            row = catalog.db.execute("SELECT * FROM runs WHERE run_id=? AND status='success'", (identifier(rid),)).fetchone()
            if not row:
                raise PipelineError("successful_benchmark_run_required")
            result = load_json(root / "outputs" / rid / "run.json")
            verify_result(root, result, row["receipt_sha256"])
            if result.get("reused") or result["dataset_id"] != item["dataset_id"]:
                raise PipelineError("fresh_matching_benchmark_runs_required")
            runs.append(result)
    if len({r["input_signature"] for r in runs}) != 1:
        raise PipelineError("benchmark_implementation_changed")
    return runs


def assess_targets(root, request, *, persist=True):
    """Evaluate explicit human-approved scopes; never invent or relax a target."""
    if (not isinstance(request, dict) or set(request) != {"assessment_id", "approved_by", "approval_ref", "targets"}
            or not request["approved_by"] or not request["approval_ref"] or not isinstance(request["targets"], list)
            or not request["targets"]):
        raise PipelineError("explicit_approved_targets_required")
    aid = identifier(request["assessment_id"])
    outcomes, seen = [], set()
    for target in request["targets"]:
        if set(target) != {"dataset_id", "baseline_id", "candidate_id", "source_signature", "baseline_sha256", "max_duration_ratio", "max_memory_ratio"}:
            raise PipelineError("invalid_target_fields")
        did = identifier(target["dataset_id"])
        if did in seen:
            raise PipelineError("duplicate_target_dataset")
        seen.add(did)
        if any(not isinstance(target[k], str) or not re.fullmatch(r"[0-9a-f]{64}", target[k]) for k in ("source_signature", "baseline_sha256")):
            raise PipelineError("approved_baseline_fingerprint_required")
        baseline_path = checked_path(root / "benchmarks" / (identifier(target["baseline_id"]) + ".json"))
        if sha_file(baseline_path) != target["baseline_sha256"]:
            raise PipelineError("approved_baseline_changed")
        for name in ("max_duration_ratio", "max_memory_ratio"):
            v = target[name]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
                raise PipelineError("positive_finite_target_required")
        baseline, candidate = [recorded_runs(root, target[k]) for k in ("baseline_id", "candidate_id")]
        if target["baseline_id"] == target["candidate_id"] or set(r["run_id"] for r in baseline) & set(r["run_id"] for r in candidate):
            raise PipelineError("distinct_baseline_candidate_required")
        if any(r["dataset_id"] != did for r in baseline + candidate):
            raise PipelineError("target_dataset_mismatch")
        if any(r["semantic_signature"] != target["source_signature"] for r in baseline + candidate):
            raise PipelineError("approved_scope_mismatch")
        result = compare(baseline, candidate)
        exact_artifacts = all(len({r["files"][name] for r in baseline + candidate}) == 1 for name in ("data.parquet", "quarantine.jsonl"))
        measured = all(r["memory"]["samples"] > 0 and r["memory"]["sampling_errors"] == 0
                       and r["memory"]["peak_rss_bytes"] is not None for r in baseline + candidate)
        before, after = result["baseline"], result["candidate"]
        duration_ok = after["median_duration_ms"] <= before["median_duration_ms"] * target["max_duration_ratio"]
        memory_ok = measured and after["max_peak_rss_bytes"] <= before["max_peak_rss_bytes"] * target["max_memory_ratio"]
        passed = result["status"] == "comparable" and exact_artifacts and duration_ok and memory_ok
        outcomes.append({"dataset_id": did, "status": "met" if passed else "not_met", "target": target,
                         "coverage": baseline[0]["coverage"], "max_input_rows": baseline[0]["max_input_rows"],
                         "exact_parquet_and_quarantine": exact_artifacts, "memory_measured": measured,
                         "duration_met": duration_ok, "memory_met": memory_ok, "comparison": result})
    report = {"schema_version": "jipdam_target_assessment_v1", "assessment_id": aid, "request": request,
              "targets_status": "verified" if all(x["status"] == "met" for x in outcomes) else "not_met", "outcomes": outcomes,
              "m1_complete": None, "m1_completion_source": "Task AC evidence; not inferred from performance alone"}
    if persist:
        with writer_lock(root):
            path = root / "assessments" / (aid + ".json")
            if path.exists() and load_json(path)["request"] != request:
                raise PipelineError("assessment_id_conflict")
            atomic_json(path, report)
    return report


def performance_report(root, assessment_id=None):
    paths = sorted((root / "benchmarks").glob("*.json"))
    values = [load_json(p) for p in paths]
    paths = ([checked_path(root / "assessments" / (identifier(assessment_id) + ".json"))] if assessment_id
             else sorted((root / "assessments").glob("*.json")))
    assessments = [assess_targets(root, load_json(p)["request"], persist=False) for p in paths]
    return {"schema_version": "jipdam_performance_report_v1", "benchmarks": values, "assessments": assessments,
            "baseline_status": "recorded" if values else "baseline_unavailable",
            "targets_status": (assessments[0]["targets_status"] if len(assessments) == 1 else
                               "select_assessment_id" if assessments else "pending_user_targets"),
            "m1_complete": None if assessments else False, "cloud_status": "not_configured"}

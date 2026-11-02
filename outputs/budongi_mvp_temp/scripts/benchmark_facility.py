"""Bounded BENCH-FACILITY-001 coordinator using the existing managed harness.

Run this committed script from the clean experiment root. Requests/ledgers remain
under its ignored .local_runtime. It never applies a model result or approves it
without a separate, explicit coordinator command.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "outputs/budongi_mvp_temp/src"))

from jipdam_harness.contracts import HarnessError
from jipdam_harness.execution import CodexCLIProvider, codex_prompt, redact, run_process
from jipdam_harness.isolation import git, pack_context, snapshot
from jipdam_harness.managed import ManagedStore, validate
from jipdam_harness.observability import MetricsStore, encoded, hashed
from jipdam_harness.orchestrator import Orchestrator

APP = "outputs/budongi_mvp_temp/"
SPEC = APP + "docs/specs/29_facility_package_validation_spec.md"
EVAL = APP + "tests/test_team_package_acceptance.py"
CODE = APP + "src/budongi/team_package.py"
PUBLIC_TEST = APP + "tests/test_team_package.py"
ACS = [f"FACILITY-PACKAGE-001-AC-{n:02}" for n in range(1, 7)]
ORDER = [("A1", "repeat"), ("B1", "once"), ("B2", "once"), ("A2", "repeat")]
MODEL = "gpt-6.1-terra"
REASONING = "high"


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


class FixedCodex(CodexCLIProvider):
    def __init__(self, prompt_log=None):
        super().__init__(model=MODEL)
        self.prompt_log = Path(prompt_log) if prompt_log else None
        self.prompt_receipts = []

    def _command(self):
        return [*super()._command(), "-c", 'model_reasoning_effort="high"',
                "-c", 'model_provider="openai"',
                "-c", "features.memories=false", "-c", "features.external_agent_memory_import=false",
                "-c", "features.multi_agent=false", "-c", "features.multi_agent_v2=false"]

    def execute(self, task, context, cwd, should_stop):
        sent = codex_prompt(task, context)
        repeated = redact(str(task.get("objective", "")) + "\n\n" + context)
        receipt = {"attempt": task.get("_attempt", 1), "objective_mode": task.get("execution", {}).get("objective_mode", "repeat"),
                   "sha256": hashlib.sha256(sent.encode()).hexdigest(), "bytes": len(sent.encode()),
                   "duplicate_removed": sent != repeated, "configured_model": self.model, "reasoning": REASONING}
        self.prompt_receipts.append(receipt)
        if self.prompt_log:
            self.prompt_log.parent.mkdir(parents=True, exist_ok=True)
            with self.prompt_log.open("a", encoding="utf-8") as stream:
                stream.write(encoded(receipt) + "\n"); stream.flush(); os.fsync(stream.fileno())
        return super().execute(task, context, cwd, should_stop)


def preflight(root):
    p = FixedCodex()
    rc, out, _, stop = run_process([*p._command(), "--version"], root, None, 10, lambda: None)
    if rc or stop or out.strip() != "codex-cli 0.164.0":
        raise ValueError("unsupported_cli_version")
    rc, out, err, stop = run_process([*p._command(), "login", "status"], root, None, 10, lambda: None)
    if rc or stop or "chatgpt" not in (out + err).lower():
        raise ValueError("chatgpt_authentication_required")
    if any(os.environ.get(name) for name in ("CODEX_API_KEY", "OPENAI_API_KEY")):
        raise ValueError("api_environment_not_allowed_for_subscription_benchmark")
    rc, out, _, stop = run_process([*p._command(), "features", "list"], root, None, 10, lambda: None)
    if rc or stop or not re.search(r"^memories\s+.*\bfalse\s*$", out, re.M):
        raise ValueError("memory_state_not_verified")
    if not re.search(r"^multi_agent\s+.*\bfalse\s*$", out, re.M):
        raise ValueError("single_agent_state_not_verified")
    return {"cli_version": "0.164.0", "authentication": "chatgpt", "configured_model": MODEL,
            "observed_model": None, "reasoning": REASONING, "memories": False, "native_multi_agent": False,
            "scope": "managed_codex_cli_turn_usage", "outside_scope_possible": True}


def task_body(label, mode, objective):
    return {"task_id": "BENCH-FACILITY-001-" + label, "objective": objective,
            "scope": {"allowed_paths": [CODE, PUBLIC_TEST], "forbidden_paths": []},
            "context_files": [], "acceptance_criteria": ACS,
            "execution": {"preferred_provider": "codex", "fallback_provider": "mock", "allow_fallback": False,
                          "resume_session": False, "max_attempts": 2, "timeout_seconds": 600,
                          "total_timeout_seconds": 1500, "sandbox": "workspace-write", "model": MODEL,
                          "model_reasoning_effort": REASONING, "objective_mode": mode},
            "safety": {"require_approval": True, "allow_destructive_operations": False},
            "validation": [{"argv": ["python", "-m", "unittest", "discover", "-s", APP + "tests", "-p", name], "acs": ACS}
                           for name in ("test_team_package_acceptance.py", "test_team_package.py", "test_managed_providers.py")]}


def objective(root):
    return ("Implement BENCH-FACILITY-001 under parent Jira KAN-31. The parent owns Jira/Git/wiki; do not call external services or git writes. "
            "Create only " + CODE + " and " + PUBLIC_TEST + ". Use stdlib. Read the fixed contract below; do not edit specs/evaluator/harness. "
            "Implement validate_package and its module CLI, add meaningful public unittest tests, and run both frozen acceptance and public tests. Do not spawn subagents or call other models. "
            "Do not collect real data, read credentials, access network/DB, install packages, commit, push, merge or change runtime policies. "
            "This is the complete task contract; do not expand the feature.\n\n" + (root / SPEC).read_text(encoding="utf-8"))


def seal(root, directory):
    if (root / CODE).exists() or (root / PUBLIC_TEST).exists():
        raise ValueError("benchmark_must_start_without_implementation")
    if git(root, "status", "--porcelain").strip():
        raise ValueError("benchmark_source_must_be_clean")
    pre = preflight(root)
    sources = [SPEC, EVAL, APP + "docs/specs/30_context_benchmark_spec.md", APP + "scripts/benchmark_facility.py",
               APP + "src/jipdam_harness/execution.py", APP + "src/jipdam_harness/managed.py", "AGENTS.md", APP + "AGENTS.md"]
    body = objective(root)
    tasks, prompts = [], {}
    for label, mode in ORDER:
        task = validate(task_body(label, mode, body), root)
        context = pack_context(task, root)
        prompt = codex_prompt(task, context)
        prompts[label] = {"sha256": hashlib.sha256(prompt.encode()).hexdigest(), "bytes": len(prompt.encode()), "mode": mode}
        tasks.append(task)
    repeat = codex_prompt(tasks[0], pack_context(tasks[0], root))
    once = codex_prompt(tasks[1], pack_context(tasks[1], root))
    if repeat != body + "\n\n" + once:
        raise ValueError("prompt_delta_is_not_objective_only")
    if prompts["A1"] != prompts["A2"] or prompts["B1"] != prompts["B2"]:
        raise ValueError("repetition_prompt_changed")
    content = {"schema_version": "facility_benchmark_v1", "original_item_id": "BENCH-FACILITY-001",
               "original_item_count": 1, "trial_count": 4, "order": [x[0] for x in ORDER],
               "start_sha": git(root, "rev-parse", "HEAD").strip(), "environment": pre,
               "sources": {name: file_sha(root / name) for name in sources}, "prompts": prompts,
               "objective_sha256": hashlib.sha256(body.encode()).hexdigest(),
               "evaluation_sha256": file_sha(root / EVAL), "ac_sha256": hashed(ACS),
               "controlled_policy": {"max_attempts": 2, "timeout_seconds": 600, "total_timeout_seconds": 1500,
                                     "resume_session": False, "allow_fallback": False, "sandbox": "workspace-write"},
               "task_hashes": {t["task_id"]: hashed(t) for t in tasks}}
    content["manifest_sha256"] = hashed(content)
    manifest = directory / "sealed-manifest.json"
    if manifest.exists() and json.loads(manifest.read_text(encoding="utf-8")) != content:
        raise ValueError("experiment_manifest_is_immutable")
    write(manifest, content)
    store = ManagedStore(directory / "managed", root)
    metrics = MetricsStore(store.directory)
    for task in tasks:
        label = task["task_id"].rsplit("-", 1)[1]
        metrics.suite({"suite_id": "FACILITY-PILOT-" + label, "suite_version": "v1",
                       "items": [{"item_id": "BENCH-FACILITY-001", "task_ids": [task["task_id"]], "difficulty": "M",
                                  "ac_sha256": content["ac_sha256"], "evaluation_sha256": content["evaluation_sha256"]}]})
        write(directory / "requests" / (label + ".json"), task)
        store.create(task)
    return content


def checked(root, directory):
    content = json.loads((directory / "sealed-manifest.json").read_text(encoding="utf-8"))
    expected = content.pop("manifest_sha256")
    if hashed(content) != expected: raise ValueError("manifest_changed")
    content["manifest_sha256"] = expected
    if git(root, "rev-parse", "HEAD").strip() != content["start_sha"] or git(root, "status", "--porcelain").strip():
        raise ValueError("benchmark_base_changed")
    for name, digest in content["sources"].items():
        if file_sha(root / name) != digest: raise ValueError("sealed_source_changed")
    if preflight(root) != content["environment"]: raise ValueError("benchmark_environment_changed")
    return content


def smoke(root, directory):
    preflight(root)
    store = ManagedStore(directory / "smoke", root)
    task = task_body("SMOKE", "repeat", "No tools or file access. Reply exactly BENCH_SMOKE_OK. This is an authorized KAN-31 Usage preflight, no implementation.")
    task["execution"].update(sandbox="read-only", max_attempts=1, timeout_seconds=120, total_timeout_seconds=180)
    task["acceptance_criteria"] = ["Smoke response and official usage"]
    task["validation"] = [{"argv": ["python", "-m", "unittest", "discover", "-s", APP + "tests", "-p", "test_managed_providers.py"], "acs": task["acceptance_criteria"]}]
    store.create(task)
    if store.get(task["task_id"])["state"] == "READY":
        Orchestrator(store, {"codex": FixedCodex(directory / "prompt-receipts/smoke.jsonl")}).run(task["task_id"])
    report = store.export(task["task_id"])
    result = {"state": report["state"], "measurement": report.get("measurement"),
              "response_ok": "BENCH_SMOKE_OK" in report["result"].get("summary", ""),
              "changed_files": report["result"].get("changed_files"), "not_part_of_feature_trial": True}
    write(directory / "smoke-receipt.json", result)
    return result


def rejected_review(root, directory, label, content, store):
    """A failed review permits scheduling, never a verified-success approval."""
    path = directory / 'results' / (label + '-review.json')
    if not path.is_file():
        return None
    request = json.loads(path.read_text(encoding='utf-8'))
    expected = root / '.local_runtime/observability-evaluations' / ('BENCH-FACILITY-001-' + label + '-review-rejected.json')
    if request.get('evidence_file') != expected.relative_to(root).as_posix() or file_sha(expected) != request.get('evidence_sha256'):
        raise ValueError('review_evidence_changed')
    artifact = json.loads(expected.read_text(encoding='utf-8'))
    item = MetricsStore(store.directory).suite_report('FACILITY-PILOT-' + label)['items'][0]
    if (artifact != {k: v for k, v in request.items() if k not in ('evidence_file', 'evidence_sha256')}
            or artifact.get('suite_id') != 'FACILITY-PILOT-' + label
            or artifact.get('item_id') != 'BENCH-FACILITY-001'
            or artifact.get('run_revisions') != item['run_revisions']
            or artifact.get('evaluation_sha256') != content['evaluation_sha256']
            or artifact.get('independent') is not True
            or artifact.get('gates', {}).get('review') is not False
            or artifact.get('gates', {}).get('approval') is not False):
        raise ValueError('review_subject_changed')
    return artifact


def run_trial(root, directory, label):
    content = checked(root, directory)
    store = ManagedStore(directory / "managed", root)
    task_id = "BENCH-FACILITY-001-" + label
    row = store.get(task_id)
    if hashed(row["task"]) != content["task_hashes"][task_id]: raise ValueError("task_changed")
    for earlier in content["order"][:content["order"].index(label)]:
        if (store.get("BENCH-FACILITY-001-" + earlier)["state"] != "COMPLETED"
                and rejected_review(root, directory, earlier, content, store) is None):
            raise ValueError("earlier_trial_requires_independent_approval")
    if row["state"] != "READY": raise ValueError("trial_already_started")
    started = time.monotonic()
    provider = FixedCodex(directory / "prompt-receipts" / (label + ".jsonl"))
    report = Orchestrator(store, {"codex": provider}).run(task_id)
    tree = Path(report["worktree"]) if report.get("worktree") else None
    immutable = bool(tree and file_sha(tree / EVAL) == content["evaluation_sha256"])
    result = {"label": label, "task_id": task_id, "start_sha": content["start_sha"], "state": report["state"],
              "measurement": report["measurement"], "evaluator_unchanged": immutable,
              "wall_seconds": time.monotonic() - started, "worktree": str(tree) if tree else None,
              "changed_files": report["result"].get("changed_files", {}),
              "validation_passed": report["result"].get("validation_passed") is True,
              "prompt_receipts": provider.prompt_receipts,
              "prompt_matches_seal": bool(provider.prompt_receipts and provider.prompt_receipts[0]["sha256"] == content["prompts"][label]["sha256"]),
              "checks": [{"argv": c["argv"], "exit_code": c["exit_code"]} for c in report["result"].get("validation", [])]}
    write(directory / "results" / (label + ".json"), result)
    return result


def reject_trial(root, directory, label, reviewer, reason):
    content = checked(root, directory)
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,95}', reason):
        raise ValueError('static_review_reason_required')
    store = ManagedStore(directory / 'managed', root)
    task_id = 'BENCH-FACILITY-001-' + label
    row = store.export(task_id)
    if row['state'] not in ('REVIEW_REQUIRED', 'FAILED', 'BLOCKED', 'CANCELLED'):
        raise ValueError('review_requires_finished_execution')
    result = json.loads((directory / 'results' / (label + '.json')).read_text(encoding='utf-8'))
    if result.get('prompt_matches_seal') is not True:
        raise ValueError('actual_prompt_did_not_match_seal')
    metrics = MetricsStore(store.directory)
    suite_id = 'FACILITY-PILOT-' + label
    item = metrics.suite_report(suite_id)['items'][0]
    artifact = dict(suite_id=suite_id, item_id='BENCH-FACILITY-001', run_revisions=item['run_revisions'],
                    evaluation_sha256=content['evaluation_sha256'], independent=True, evaluator=reviewer,
                    gates={k: False for k in ('ac', 'regression', 'security', 'scope', 'review', 'approval')},
                    reason=reason)
    evidence = root / '.local_runtime/observability-evaluations' / (task_id + '-review-rejected.json')
    write(evidence, artifact)
    request = dict(artifact, evidence_file=evidence.relative_to(root).as_posix(), evidence_sha256=file_sha(evidence))
    outcome = metrics.outcome(request)
    write(directory / 'results' / (label + '-review.json'), request)
    return dict(state=row['state'], review_outcome='rejected', reason=reason,
                verified_success_count=outcome['verified_success_count'])


def approve_trial(root, directory, label, reviewer):
    content = checked(root, directory)
    store = ManagedStore(directory / "managed", root)
    task_id = "BENCH-FACILITY-001-" + label
    row = store.get(task_id)
    tree = Path(row["worktree"])
    result = json.loads((directory / "results" / (label + ".json")).read_text(encoding="utf-8"))
    if result.get("prompt_matches_seal") is not True:
        raise ValueError("actual_prompt_did_not_match_seal")
    if file_sha(tree / EVAL) != content["evaluation_sha256"] or not (tree / CODE).is_file() or not (tree / PUBLIC_TEST).is_file():
        raise ValueError("evaluation_or_deliverable_missing")
    if set(snapshot(tree)) != {CODE, PUBLIC_TEST}: raise ValueError("scope_or_deliverable_mismatch")
    if row["state"] == "REVIEW_REQUIRED": store.approve(task_id, reviewer)
    elif row["state"] != "COMPLETED": raise ValueError("trial_not_reviewable")
    metrics = MetricsStore(store.directory)
    suite_id = "FACILITY-PILOT-" + label
    item = metrics.suite_report(suite_id)["items"][0]
    artifact = {"suite_id": suite_id, "item_id": "BENCH-FACILITY-001", "run_revisions": item["run_revisions"],
                "evaluation_sha256": content["evaluation_sha256"], "independent": True, "evaluator": reviewer,
                "gates": {k: True for k in ("ac", "regression", "security", "scope", "review", "approval")}}
    evidence = root / ".local_runtime/observability-evaluations" / (task_id + ".json")
    write(evidence, artifact)
    request = {**artifact, "evidence_file": evidence.relative_to(root).as_posix(), "evidence_sha256": file_sha(evidence)}
    outcome = metrics.outcome(request)
    receipt = store.export(task_id)
    write(directory / "results" / (label + "-approved.json"), {"task_id": task_id, "measurement": receipt["measurement"], "outcome": outcome})
    return {"state": receipt["state"], "outcome": outcome, "measurement": receipt["measurement"]}


def report_trials(root, directory):
    content = checked(root, directory)
    store = ManagedStore(directory / "managed", root)
    metrics = MetricsStore(store.directory)
    trials = []
    for label, mode in ORDER:
        row = store.export("BENCH-FACILITY-001-" + label)
        suite = metrics.suite_report("FACILITY-PILOT-" + label)
        m = row["measurement"]
        review = rejected_review(root, directory, label, content, store)
        trials.append({"label": label, "objective_mode": mode, "state": row["state"],
                       "coverage_state": m["coverage_state"], "known_tokens": m.get("known_observed_tokens"),
                       "complete_tokens": m.get("complete_run_tokens"), "retry_count": m.get("retry_count"),
                       "failed_attempt_tokens_known": m.get("failed_attempt_tokens_known"),
                       "review_outcome": 'rejected' if review else 'approved' if suite['verified_success_count'] == 1 else 'pending',
                       "review_rejected_tokens": m.get('known_observed_tokens') if review else None,
                       "wall_seconds": m.get("task_wall_time_seconds"), "human_attention_minutes": None,
                       "verified_success": suite["verified_success_count"] == 1,
                       "tokens_per_verified_success": suite["tokens_per_verified_success"],
                       "usage": [o["normalized_usage"] for i in m.get("invocations", []) for o in i["usage_observations"]]})
    paired = []
    for n in (1, 2):
        a = next(t for t in trials if t["label"] == "A" + str(n))
        b = next(t for t in trials if t["label"] == "B" + str(n))
        eligible = all(t["coverage_state"] == "complete" and t["verified_success"] for t in (a, b))
        paired.append({"pair": n, "comparable": eligible,
                       "baseline_tokens": a["complete_tokens"], "candidate_tokens": b["complete_tokens"],
                       "token_reduction_pct": (a["complete_tokens"] - b["complete_tokens"]) / a["complete_tokens"] * 100
                       if eligible and a["complete_tokens"] else None})
    result = {"manifest_sha256": content["manifest_sha256"], "start_sha": content["start_sha"],
              "original_item_count": 1, "trial_count": 4, "trials": trials, "paired": paired,
              "conclusion": "pilot_only_no_statistical_or_general_causal_superiority_claim",
              "outside_scope": ["this_app_planning", "jira", "git", "hidden_provider_calls", "human_active_time"]}
    write(directory / "comparison.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", default=".local_runtime/facility-benchmark")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "seal", "smoke", "report"): sub.add_parser(name)
    for name in ("run", "approve", "reject"):
        item = sub.add_parser(name); item.add_argument("--trial", choices=[x[0] for x in ORDER], required=True)
        if name in ('approve', 'reject'): item.add_argument("--reviewer", required=True)
        if name == 'reject': item.add_argument('--reason', required=True)
    args = parser.parse_args(argv)
    directory = (ROOT / args.state_dir).resolve()
    try:
        if not directory.is_relative_to(ROOT / ".local_runtime"): raise ValueError("state_directory_outside_runtime")
        if args.command == "preflight": result = preflight(ROOT)
        elif args.command == "seal": result = seal(ROOT, directory)
        elif args.command == "smoke": result = smoke(ROOT, directory)
        elif args.command == "run": result = run_trial(ROOT, directory, args.trial)
        elif args.command == "approve": result = approve_trial(ROOT, directory, args.trial, args.reviewer)
        elif args.command == 'reject': result = reject_trial(ROOT, directory, args.trial, args.reviewer, args.reason)
        else: result = report_trials(ROOT, directory)
        print(encoded(result))
        return 0
    except (HarnessError, ValueError, OSError, KeyError):
        print(encoded({"status": "error", "error": "benchmark_precondition_or_execution_failed"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

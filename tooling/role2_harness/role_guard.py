"""Role separation guard for role-2 multi-LLM builds (ROLE2-COLLECT-001-REQ-08, ADR-025).

Wraps agy-outsource / agy-delegate calls. Model families always come from the actual
model slug, never from the tool name ("agy"), which closes the gap where an Anthropic
model run through agy is labelled as Gemini.

  python tooling/role2_harness/role_guard.py check --contractor agy:gemini-3.8-flash --auditor sonnet --referee haiku
  python tooling/role2_harness/role_guard.py outsource run PLAN --contractor agy:gemini-3.8-flash -- -j 4 --timeout 30
  python tooling/role2_harness/role_guard.py outsource run PLAN --contractor agy:claude-sonnet-5-5 \
      --waive-r2-overlap "2026-10-30 user decision: ..." -- -j 4   # auditor may share the contractor's family
  python tooling/role2_harness/role_guard.py outsource audit PLAN --auditor sonnet
  python tooling/role2_harness/role_guard.py outsource triage PLAN --unit UNIT --referee haiku --contractor agy:gemini-3.8-flash
  python tooling/role2_harness/role_guard.py verify-run PLAN --contractor agy:gemini-3.8-flash
  python tooling/role2_harness/role_guard.py delegate --model gemini-3.8-flash-medium -- run -w DIR -f TASK.md ...
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

LEAD = "claude-opus-5-5"
REPO = Path(__file__).resolve().parents[2]
SKILLS = Path(os.environ.get("CLAUDE_SKILLS_DIR", Path.home() / ".claude" / "skills"))
OUTSOURCE = SKILLS / "agy-outsource" / "scripts" / "outsource.py"
AGY_TASK = SKILLS / "agy-delegate" / "scripts" / "agy_task.py"
BANNED_PREFIXES = ("gpt-6",)  # GMS is excluded for this work (2026-10-29 user decision)
FORBIDDEN_INPUT_PARTS = {"hidden", "hidden.sealed", ".env", "credentials", "data", "raw", "logs", ".local_runtime"}


class RoleError(ValueError):
    """A role assignment that would let a model judge its own family's work."""


def identify(model: str | None) -> tuple[str, str]:
    """Return (vendor, family) from a model slug or a claude alias."""
    m = (model or "").strip().lower()
    if not m:
        raise RoleError("model_required")
    if m.startswith(BANNED_PREFIXES):
        raise RoleError("model_banned:gms")
    for family in ("opus", "sonnet", "haiku", "fable"):
        if family in m:
            return "anthropic", family
    if m.startswith("gemini"):
        return "google", "gemini"
    if m.startswith("gpt-oss"):
        return "openai", "gpt-oss"
    raise RoleError(f"unknown_model:{m}")


def parse_contractor(spec: str) -> tuple[str, str]:
    """'agy:<slug>' or 'claude:<alias>' -> (tool, model)."""
    tool, _, model = spec.partition(":")
    if tool not in {"agy", "claude"} or not model:
        raise RoleError("contractor_must_be_agy_or_claude_with_model")
    return tool, model


def check_roles(*, contractor: str, auditor: str | None = None, referee: str | None = None,
                lead: str = LEAD, waive_overlap: str | None = None) -> dict:
    """R1-R3: contractor != lead family; auditor/referee are claude, not lead, not gemini, all distinct.

    waive_overlap (a non-empty reason string) relaxes ONE clause of R2: the auditor may share the
    CONTRACTOR's family, because the audit judges the lead's tests before any code exists. The hard
    core of R2 is never waived: the auditor stays Anthropic, never the lead's family, never gemini.
    The waiver is returned in the result so callers can put it in the run log and the ledger.
    """
    tool, model = parse_contractor(contractor)
    lead_family = identify(lead)[1]
    vendor, family = identify(model)
    if family == lead_family:
        raise RoleError("R1_contractor_is_lead_family")
    if tool == "agy" and vendor == "anthropic" and family == "opus":
        raise RoleError("R1_opus_via_agy_banned")
    result = {"contractor": {"tool": tool, "model": model, "vendor": vendor, "family": family}}
    if auditor is not None:
        a_vendor, a_family = identify(auditor)
        if a_vendor != "anthropic" or a_family == lead_family:
            raise RoleError("R2_auditor_family_conflict")
        if a_family == family:
            if not (waive_overlap or "").strip():
                raise RoleError("R2_auditor_family_conflict")
            result["waiver"] = {"rule": "R2_auditor_contractor_overlap", "reason": waive_overlap,
                                "auditor_family": a_family, "contractor_family": family}
        result["auditor"] = {"model": auditor, "family": a_family}
    if referee is not None:
        r_vendor, r_family = identify(referee)
        taken = {lead_family, family} | ({result["auditor"]["family"]} if auditor else set())
        if r_vendor != "anthropic" or r_family in taken:
            raise RoleError("R3_referee_family_conflict")
        result["referee"] = {"model": referee, "family": r_family}
    return result


def check_inputs(paths: list[str], *, workdir: str | None) -> None:
    """R5: agy never sees hidden tests, keys or collected data; its work dir is outside the repo."""
    if workdir is not None:
        resolved = Path(workdir).resolve()
        if resolved == REPO or REPO in resolved.parents:
            raise RoleError("R5_workdir_inside_repo")
    for raw in paths:
        parts = {p.lower() for p in Path(raw).parts}
        if parts & FORBIDDEN_INPUT_PARTS or Path(raw).name.lower().startswith(".env"):
            raise RoleError(f"R5_forbidden_input:{Path(raw).name}")


def _family_of_attempt(unit_dir: Path) -> str | None:
    """Actual contractor model of the latest attempt: claude.json model, agy block model, or events init.model."""
    attempts = sorted(unit_dir.glob("attempt_*.json"), key=lambda p: int(p.stem.split("_")[1].split(".")[0])
                      if p.stem.split("_")[1].split(".")[0].isdigit() else 0)
    attempts = [p for p in attempts if p.name.count(".") == 1]
    if not attempts:
        return None
    latest = attempts[-1]
    claude = latest.with_name(latest.stem + ".claude.json")
    if claude.is_file():
        model = json.loads(claude.read_text(encoding="utf-8")).get("model")
        return model
    record = json.loads(latest.read_text(encoding="utf-8"))
    model = (record.get("agy") or {}).get("model")
    if model:
        return model
    for events in sorted(unit_dir.glob(f"{latest.stem}.agy_task/*/events.jsonl")):
        for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "init" and event.get("model"):
                return event["model"]
    log = latest.with_name(f"{latest.stem}.agy.log")
    if log.is_file():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if "] workdir=" in line and " model=" in line:
                return line.split(" model=", 1)[1].split()[0]
    return None


def verify_run(run_dir: Path, *, contractor: str) -> dict:
    """Compare every unit's actual contractor model with the routed one (post-run R1 check)."""
    _, routed = parse_contractor(contractor)
    routed_family = identify(routed)[1]
    lead_family = identify(LEAD)[1]
    report = {"routed": routed, "units": {}, "violations": 0, "unverified": 0}
    for unit_dir in sorted((run_dir / "units").glob("*")):
        model = _family_of_attempt(unit_dir)
        if model is None:
            report["units"][unit_dir.name] = "model_unverified"
            report["unverified"] += 1
            continue
        try:
            family = identify(model)[1]
        except RoleError as exc:
            report["units"][unit_dir.name] = str(exc)
            report["violations"] += 1
            continue
        ok = family == routed_family and family != lead_family
        report["units"][unit_dir.name] = {"model": model, "family": family, "ok": ok}
        report["violations"] += 0 if ok else 1
    return report


def _run(argv: list[str]) -> int:
    return subprocess.call([sys.executable, "-X", "utf8", *argv])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="role_guard")
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("check")
    c.add_argument("--contractor", required=True)
    c.add_argument("--auditor")
    c.add_argument("--referee")
    c.add_argument("--waive-r2-overlap", dest="waive", metavar="REASON")
    o = sub.add_parser("outsource")
    o.add_argument("action", choices=["run", "audit", "triage"])
    o.add_argument("plan")
    o.add_argument("--unit", help="triage only: the unit to referee")
    o.add_argument("--contractor")
    o.add_argument("--auditor")
    o.add_argument("--referee")
    o.add_argument("--waive-r2-overlap", dest="waive", metavar="REASON",
                   help="allow the auditor to share the contractor's family; the reason is logged")
    v = sub.add_parser("verify-run")
    v.add_argument("plan")
    v.add_argument("--contractor", required=True)
    v.add_argument("--run-dir")
    d = sub.add_parser("delegate")
    d.add_argument("--model", required=True)
    args, unknown = parser.parse_known_args(argv)
    args.rest = unknown
    try:
        if args.command == "check":
            print(json.dumps(check_roles(contractor=args.contractor, auditor=args.auditor, referee=args.referee,
                                         waive_overlap=args.waive)))
            return 0
        if args.command == "verify-run":
            run_dir = Path(args.run_dir) if args.run_dir else Path(args.plan).parent / ".agy_outsource"
            report = verify_run(run_dir, contractor=args.contractor)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["violations"] == 0 else 2
        rest = [a for a in getattr(args, "rest", []) if a != "--"]
        if args.command == "delegate":
            identify(args.model)
            check_roles(contractor=f"agy:{args.model}")
            workdir = next((rest[i + 1] for i, a in enumerate(rest[:-1]) if a in {"-w", "--workdir"}), None)
            inputs = [rest[i + 1] for i, a in enumerate(rest[:-1]) if a in {"-i", "--input"}]
            check_inputs(inputs, workdir=workdir)
            return _run([str(AGY_TASK), "--model", args.model, *rest])
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        roles = plan.get("roles") or {}
        if identify(roles.get("lead"))[1] != identify(LEAD)[1]:
            raise RoleError("plan_lead_must_be_opus")
        if args.action == "run":
            info = check_roles(contractor=args.contractor, auditor=roles.get("auditor"), waive_overlap=args.waive)
            if info.get("waiver"):
                print(json.dumps({"status": "r2_overlap_waived", **info["waiver"]}, ensure_ascii=False))
            tool, model = info["contractor"]["tool"], info["contractor"]["model"]
            extra = ["--model", model] if tool == "agy" else ["--contractor", f"claude:{model}"]
            return _run([str(OUTSOURCE), "run", args.plan, *extra, *rest])
        if args.action == "audit":
            auditor = args.auditor or roles.get("auditor")
            if args.contractor:
                check_roles(contractor=args.contractor, auditor=auditor, waive_overlap=args.waive)
            return _run([str(OUTSOURCE), "audit", args.plan, "--auditor", auditor, *rest])
        if not args.unit or not args.referee or not args.contractor:
            raise RoleError("triage_needs_unit_referee_and_contractor")
        info = check_roles(contractor=args.contractor, auditor=roles.get("auditor"), referee=args.referee,
                           waive_overlap=args.waive)
        if info.get("waiver"):
            print(json.dumps({"status": "r2_overlap_waived", **info["waiver"]}, ensure_ascii=False))
        return _run([str(OUTSOURCE), "triage", args.plan, args.unit, "--auditor", args.referee, *rest])
    except RoleError as exc:
        print(json.dumps({"status": "role_violation", "error": str(exc)}))
        return 5


if __name__ == "__main__":
    raise SystemExit(main())

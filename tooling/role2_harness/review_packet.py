"""Blind review runner (ADR-025 §3): judge an anonymized packet on a Claude model.

The packet carries only the material to judge (producer identities removed); the run
happens in a fresh folder outside the repository with tools off; the actual model is
verified afterwards and the verdict is appended to the hash-chained ledger.

  python tooling/role2_harness/review_packet.py judge --packet P.json --model sonnet \
      --producers gemini,opus --out V.json [--ledger .local_runtime/role2/xval/verdicts.jsonl]

The packet JSON must contain 'prompt' (what the judge is asked, ending with the answer
rules) and 'schema' (the JSON schema the judge's answer must follow). Everything else in
the packet is given to the judge verbatim as context.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SKILLS = Path(os.environ.get("CLAUDE_SKILLS_DIR", Path.home() / ".claude" / "skills"))
sys.path.insert(0, str(SKILLS / "agy-outsource" / "scripts"))
sys.path.insert(0, str(HERE))

import ledger  # noqa: E402  (tooling/role2_harness)
import roles   # noqa: E402  (agy-outsource skill)

LEAD_FAMILY = "opus"


def judge(packet_path: Path, *, model: str, producers: list[str], out: Path,
          ledger_path: Path | None) -> dict:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    judge_family = roles.family(model)
    if judge_family == "gemini":
        raise roles.RoleError("judge_must_be_claude")
    for producer in producers:
        if judge_family == roles.family(producer):
            raise roles.RoleError(f"R4_judge_is_producer_family:{producer}")
    prompt, schema = packet["prompt"], packet["schema"]
    context = {k: v for k, v in packet.items() if k not in {"prompt", "schema"}}
    full_prompt = (prompt + "\n\n## Material (anonymous drafts; judge on merit only)\n\n"
                   + json.dumps(context, ensure_ascii=False, indent=1))
    with tempfile.TemporaryDirectory(prefix="role2-review-") as tmp:
        if REPO in Path(tmp).resolve().parents:
            raise roles.RoleError("review_dir_inside_repo")
        res = roles.run_claude(full_prompt, model=model, cwd=Path(tmp), tools="",
                               schema=schema, max_turns=2)
    roles.check_ran_as(res, "referee", model)
    answer = res.get("structured")
    if answer is None:
        answer = json.loads(res.get("result") or "null")
    if not isinstance(answer, dict):
        raise roles.ClaudeRunError("referee_answer_not_structured")
    model_used = (res.get("models") or [model])[-1]
    verdict_doc = {"packet_sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
                   "model": model_used, "answer": answer}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(verdict_doc, ensure_ascii=False, indent=1), encoding="utf-8")
    if ledger_path is not None:
        ledger.append(ledger_path, {
            "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "artifact": {"id": packet_path.name, "type": "blind_review_packet",
                         "sha256": verdict_doc["packet_sha256"]},
            "producer": {"vendor": "mixed", "family": ",".join(sorted(producers)),
                         "model": "anonymized", "tool": "packet", "effort": None},
            "referee": {"vendor": "anthropic", "family": judge_family, "model": res["model"],
                        "tool": "claude-p", "effort": None},
            "verdict": "pass", "decided_by": "referee",
            "evidence": str(out.relative_to(REPO)) if out.is_relative_to(REPO) else str(out),
            "gates": ["blind_packet", "tools_off", "ran_as_verified"]})
    return verdict_doc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="review_packet")
    sub = parser.add_subparsers(dest="command", required=True)
    j = sub.add_parser("judge")
    j.add_argument("--packet", required=True, type=Path)
    j.add_argument("--model", required=True)
    j.add_argument("--producers", required=True, help="comma-separated producer models/families")
    j.add_argument("--out", required=True, type=Path)
    j.add_argument("--ledger", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        doc = judge(args.packet, model=args.model, producers=args.producers.split(","),
                    out=args.out, ledger_path=args.ledger)
    except (roles.RoleError, roles.ClaudeRunError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 5
    print(json.dumps({"status": "ok", "model": doc["model"], "out": str(args.out)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

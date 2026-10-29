"""Append-only hash-chained verdict ledger for role-2 cross-vendor reviews (drafted by agy gemini-3.8-flash, reviewed by the Opus lead)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED = ("ts_utc", "artifact", "producer", "verdict", "evidence", "decided_by", "gates")
VERDICTS = ("pass", "fail", "needs_fix", "unverified")


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _is_valid_actor(actor: Any) -> bool:
    if not isinstance(actor, dict):
        return False
    for k in ("vendor", "family", "model", "tool"):
        if not isinstance(actor.get(k), str):
            return False
    if "effort" not in actor:
        return False
    effort = actor["effort"]
    if effort is not None and not isinstance(effort, str):
        return False
    return True


def _validate_entry(entry: dict) -> None:
    if not isinstance(entry, dict):
        raise ValueError("invalid_entry:not_a_dict")

    if "prev_sha256" in entry or "sha256" in entry:
        raise ValueError("reserved_field")

    for field in REQUIRED:
        if field not in entry:
            raise ValueError(f"invalid_entry:{field}")

    ts = entry["ts_utc"]
    if not isinstance(ts, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts):
        raise ValueError("invalid_entry:ts_utc")

    art = entry["artifact"]
    if not isinstance(art, dict):
        raise ValueError("invalid_entry:artifact")
    if not (isinstance(art.get("type"), str) and isinstance(art.get("id"), str) and isinstance(art.get("sha256"), str)):
        raise ValueError("invalid_entry:artifact")
    if not re.fullmatch(r"[0-9a-f]{64}", art["sha256"]):
        raise ValueError("invalid_entry:artifact")

    if not _is_valid_actor(entry["producer"]):
        raise ValueError("invalid_entry:producer")

    if "reviewer" in entry and entry["reviewer"] is not None:
        if not _is_valid_actor(entry["reviewer"]):
            raise ValueError("invalid_entry:reviewer")

    if "referee" in entry and entry["referee"] is not None:
        if not _is_valid_actor(entry["referee"]):
            raise ValueError("invalid_entry:referee")

    if entry["verdict"] not in VERDICTS:
        raise ValueError("invalid_entry:verdict")

    gates = entry["gates"]
    if not isinstance(gates, list) or not all(isinstance(g, str) for g in gates):
        raise ValueError("invalid_entry:gates")


def append(path: Path, entry: dict) -> dict:
    _validate_entry(entry)

    path = Path(path)
    prev = "0" * 64
    if path.exists() and path.stat().st_size > 0:
        with open(path, "rb") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if lines:
                last_record = json.loads(lines[-1].decode("utf-8"))
                prev = last_record["sha256"]

    record = dict(entry, prev_sha256=prev)
    record["sha256"] = hashlib.sha256(canonical(record)).hexdigest()

    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "ab") as f:
        f.write(canonical(record) + b"\n")
        f.flush()
        os.fsync(f.fileno())

    return record


def verify(path: Path) -> dict:
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return {"entries": 0, "ok": True, "first_bad_line": None}

    with open(path, "rb") as f:
        raw = f.read()

    lines = raw.splitlines()
    if not lines:
        return {"entries": 0, "ok": True, "first_bad_line": None}

    expected_prev = "0" * 64
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            return {"entries": len(lines), "ok": False, "first_bad_line": idx}
        try:
            record = json.loads(line.decode("utf-8"))
            if not isinstance(record, dict):
                return {"entries": len(lines), "ok": False, "first_bad_line": idx}

            if record.get("prev_sha256") != expected_prev:
                return {"entries": len(lines), "ok": False, "first_bad_line": idx}

            if "sha256" not in record:
                return {"entries": len(lines), "ok": False, "first_bad_line": idx}

            stored_sha = record["sha256"]
            record_without_sha = {k: v for k, v in record.items() if k != "sha256"}
            computed_sha = hashlib.sha256(canonical(record_without_sha)).hexdigest()
            if stored_sha != computed_sha:
                return {"entries": len(lines), "ok": False, "first_bad_line": idx}

            expected_prev = stored_sha
        except Exception:
            return {"entries": len(lines), "ok": False, "first_bad_line": idx}

    return {"entries": len(lines), "ok": True, "first_bad_line": None}


def summary(path: Path) -> dict:
    path = Path(path)
    by_artifact_type: dict[str, int] = {}
    by_verdict: dict[str, int] = {}
    pairs: dict[str, int] = {}
    entries = 0

    if path.exists() and path.stat().st_size > 0:
        with open(path, "rb") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line.decode("utf-8"))
                entries += 1

                art = record.get("artifact")
                if isinstance(art, dict) and "type" in art:
                    art_type = str(art["type"])
                    by_artifact_type[art_type] = by_artifact_type.get(art_type, 0) + 1

                verd = record.get("verdict")
                if isinstance(verd, str):
                    by_verdict[verd] = by_verdict.get(verd, 0) + 1

                prod = record.get("producer")
                prod_family = prod.get("family") if isinstance(prod, dict) else None
                prod_family_str = str(prod_family) if prod_family is not None else "none"

                rev = record.get("reviewer")
                rev_family = rev.get("family") if isinstance(rev, dict) else None
                rev_family_str = str(rev_family) if rev_family is not None else "none"

                pair_key = f"{prod_family_str}>{rev_family_str}"
                pairs[pair_key] = pairs.get(pair_key, 0) + 1

    return {
        "entries": entries,
        "by_artifact_type": by_artifact_type,
        "by_verdict": by_verdict,
        "pairs": pairs,
    }


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 2:
        print(json.dumps({"error": "invalid_arguments"}))
        return 2

    cmd = argv[0]
    target_path = Path(argv[1])

    try:
        if cmd == "verify":
            res = verify(target_path)
            print(json.dumps(res))
            return 0
        elif cmd == "summary":
            res = summary(target_path)
            print(json.dumps(res))
            return 0
        else:
            raise ValueError(f"unknown_command:{cmd}")
    except ValueError as e:
        print(json.dumps({"error": str(e)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())

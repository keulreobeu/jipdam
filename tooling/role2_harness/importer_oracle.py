"""Run the team's pinned importer unchanged against one role-2 ZIP (ROLE2-COLLECT-001-REQ-05).

The importer lives only on origin/codex/workspace-backup-20261023, so it is loaded from
its git blob, never from a working copy that could drift:

  python tooling/role2_harness/importer_oracle.py ZIP --issue 42 --work .local_runtime/role2/imp/T001
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

IMPORTER_BLOB = "f84e2010c23ee7acf36a04155899ccce06bc77f0"
REPO = Path(__file__).resolve().parents[2]


def load_importer(cache_dir: Path, *, repo: Path = REPO):
    """Materialise the pinned blob (verified by git's own object hash) and import it."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / f"importer_{IMPORTER_BLOB[:12]}.py"
    if not target.exists():
        source = subprocess.run(["git", "-C", str(repo), "cat-file", "-p", IMPORTER_BLOB], check=True,
                                capture_output=True).stdout
        target.write_bytes(source)
    spec = importlib.util.spec_from_file_location(f"team_importer_{IMPORTER_BLOB[:12]}", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _member_name(info: zipfile.ZipInfo) -> str:
    """Names stored without the UTF-8 flag were read as cp437; teammates' tools wrote UTF-8 (or cp949) bytes."""
    if info.flag_bits & 0x800:
        return info.filename
    raw = info.filename.encode("cp437")
    for encoding in ("utf-8", "cp949"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return info.filename


def _extract(archive: Path, dest: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            text = _member_name(info)
            name = PurePosixPath(text)
            if name.is_absolute() or ".." in name.parts or "\\" in text or ":" in text:
                raise ValueError("unsafe_member")
            target = dest.joinpath(*name.parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as source, target.open("xb") as sink:
                shutil.copyfileobj(source, sink)


def run_oracle(archive: Path, *, work: Path, issue: int, importer, alias: str = "t.zip") -> dict:
    """Copy and extract the ZIP the way the importer expects, register only it, and build a temp DB."""
    if work.exists() and any(work.iterdir()):
        raise ValueError("work_not_empty")
    work.mkdir(parents=True, exist_ok=True)
    copy = work / alias
    shutil.copyfile(archive, copy)
    _extract(copy, work / copy.stem)
    manifests = list((work / copy.stem).rglob("manifest.json"))
    if len(manifests) != 1:
        raise ValueError("manifest_count_mismatch")
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    if manifest.get("normalized_withheld"):
        return {"ok": None, "skipped": "license_hold_normalized_withheld"}
    normalized = [f for f in manifest.get("files", []) if f.get("path", "").startswith("normalized/")
                  and f.get("format") == "jsonl"]
    rows = normalized[0]["rows"] if len(normalized) == 1 else -1
    entry = (manifest.get("source_id"), manifest.get("batch_id"), manifest.get("record_type"), rows,
             (manifest.get("counts") or {}).get("accepted"), _sha256(copy), int(issue))
    importer.PACKAGES = {alias: entry}
    result = importer.build(work, work / "oracle.sqlite3")
    return {"ok": True, "packages_line": f"{alias!r}: {entry!r},", "result": result}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="importer_oracle")
    parser.add_argument("zip", type=Path)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        importer = load_importer(args.work.parent / "_importer")
        report = run_oracle(args.zip, work=args.work, issue=args.issue, importer=importer)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] is not False else 2


if __name__ == "__main__":
    raise SystemExit(main())

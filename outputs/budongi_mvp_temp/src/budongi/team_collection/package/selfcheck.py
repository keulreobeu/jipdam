"""Self-check of a finished team_collection_v1 ZIP package."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Callable, Iterable

from budongi.team_collection import contract as C


def _result(errors: list, members: int, lines: int, records: object) -> dict:
    return {"ok": not errors, "errors": errors,
            "counts": {"members": members, "jsonl_lines": lines}, "records": records}


def _unsafe(name: str) -> bool:
    if name.startswith("/") or "\\" in name or ":" in name:
        return True
    parts = name.split("/")
    if name.endswith("/"):
        parts = parts[:-1]
    return any(p in ("", ".", "..") for p in parts)


def _is_int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def check_zip(path: Path, *, workdir: Path,
              record_checker: Callable[[Iterable[str], dict, dict], dict]) -> dict:
    """Check the package ZIP at path, extracting into the empty workdir, and report all problems."""
    workdir = Path(workdir)
    if workdir.exists():
        if not workdir.is_dir():
            raise C.ContractError("workdir_invalid")
        if any(workdir.iterdir()):
            raise C.ContractError("workdir_not_empty")
    else:
        workdir.mkdir(parents=True)

    errors: list[str] = []
    path = Path(path)
    if not path.is_file():
        return _result(["bad_zip"], 0, 0, None)
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError):
        return _result(["bad_zip"], 0, 0, None)
    with zf:
        infos = zf.infolist()
        names = [i.filename for i in infos]
        members = sum(1 for n in names if not n.endswith("/"))

        seen: dict[str, int] = {}
        for n in names:
            if _unsafe(n):
                errors.append("unsafe_member_name:" + n)
            seen[n] = seen.get(n, 0) + 1
            if seen[n] == 2:
                errors.append("duplicate_member:" + n)
        if errors:
            return _result(errors, members, 0, None)

        try:
            bad = zf.testzip()
        except Exception:
            bad = "?"
        if bad is not None:
            return _result(["crc_mismatch:" + str(bad)], members, 0, None)

        mans = [n for n in names if n == "manifest.json" or n.endswith("/manifest.json")]
        if len(mans) != 1:
            return _result(["manifest_count"], members, 0, None)
        mname = mans[0]
        parts = mname.split("/")
        if len(parts) != 3:
            return _result(["manifest_location"], members, 0, None)
        try:
            manifest = json.loads(zf.read(mname).decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            manifest = None
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
            return _result(["manifest_invalid"], members, 0, None)
        s, b = parts[0], parts[1]
        if manifest.get("source_id") != s or manifest.get("batch_id") != b:
            return _result(["manifest_id_mismatch"], members, 0, None)
        root = s + "/" + b + "/"

        for n in names:
            target = workdir / n
            if n.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(n))

        file_names = {n for n in names if not n.endswith("/")}
        valid: list[dict] = []
        for idx, e in enumerate(manifest["files"]):
            if not (isinstance(e, dict) and isinstance(e.get("path"), str) and e["path"]
                    and _is_int(e.get("bytes")) and e["bytes"] >= 0
                    and isinstance(e.get("sha256"), str)):
                errors.append("invalid_file_entry:%d" % idx)
                continue
            valid.append(e)
            p = e["path"]
            full = root + p
            if full not in file_names:
                errors.append("missing_file:" + p)
                continue
            data = zf.read(full)
            if len(data) != e["bytes"]:
                errors.append("bytes_mismatch:" + p)
            elif hashlib.sha256(data).hexdigest() != e["sha256"]:
                errors.append("sha256_mismatch:" + p)

        listed = {root + e["path"] for e in valid}
        for n in names:
            if n.endswith("/") or n == mname:
                continue
            if n not in listed:
                errors.append("unlisted_file:" + n)

        files_by_path = {e["path"]: e for e in valid}

        norm = [e for e in valid if e["path"].startswith("normalized/")]
        withheld = manifest.get("normalized_withheld") is True
        lines: list[str] | None = None
        if withheld:
            if norm:
                errors.append("normalized_not_withheld")
        elif len(norm) != 1:
            errors.append("normalized_count")
        elif norm[0].get("format") != "jsonl":
            errors.append("normalized_format")
        else:
            ent = norm[0]
            full = root + ent["path"]
            if full in file_names:
                try:
                    text = zf.read(full).decode("utf-8")
                except UnicodeDecodeError:
                    errors.append("jsonl_decode_error")
                else:
                    lines = text.split("\n")
                    if text.endswith("\n") or text == "":
                        lines = lines[:-1]
                    rows = ent.get("rows")
                    if not _is_int(rows) or rows != len(lines):
                        errors.append("normalized_rows_mismatch")

    counts = manifest.get("counts")
    keys = ("raw", "accepted", "excluded", "rejected")
    if not (isinstance(counts, dict) and all(_is_int(counts.get(k)) and counts[k] >= 0
                                             for k in keys)):
        errors.append("invalid_counts")
    else:
        if lines is not None and counts["accepted"] + counts["rejected"] != len(lines):
            errors.append("jsonl_count_mismatch")
        if counts["raw"] != counts["accepted"] + counts["excluded"] + counts["rejected"]:
            errors.append("raw_count_mismatch")

    records = record_checker(list(lines) if lines is not None else [], manifest, files_by_path)
    if isinstance(records, dict) and records.get("ok") is False:
        errors.append("records_invalid")
    return _result(errors, members, len(lines) if lines is not None else 0, records)

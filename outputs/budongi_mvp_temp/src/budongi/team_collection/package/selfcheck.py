"""Self-check of a finished team_collection_v1 ZIP package."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Callable, Iterable

from budongi.team_collection import contract as C


def _result(errors: list, members: int, jsonl_lines: int, records: object) -> dict:
    return {"ok": not errors, "errors": errors,
            "counts": {"members": members, "jsonl_lines": jsonl_lines},
            "records": records}


def _unsafe(name: str) -> bool:
    if name.startswith("/") or "\\" in name or ":" in name:
        return True
    parts = name.split("/")
    if name.endswith("/"):
        parts = parts[:-1]
    return any(p in ("", ".", "..") for p in parts)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_entry(entry: object) -> bool:
    return (isinstance(entry, dict)
            and isinstance(entry.get("path"), str) and entry["path"] != ""
            and _is_int(entry.get("bytes")) and entry["bytes"] >= 0
            and isinstance(entry.get("sha256"), str))


def check_zip(path: Path, *, workdir: Path,
              record_checker: Callable[[Iterable[str], dict, dict], dict]) -> dict:
    """Check the package ZIP at path, extracting it into the empty workdir, and return the result."""
    workdir = Path(workdir)
    if workdir.exists():
        if not workdir.is_dir():
            raise C.ContractError("workdir_invalid")
        if any(workdir.iterdir()):
            raise C.ContractError("workdir_not_empty")
    else:
        workdir.mkdir(parents=True)

    errors: list = []
    path = Path(path)
    if not path.is_file():
        return _result(["bad_zip"], 0, 0, None)
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError):
        return _result(["bad_zip"], 0, 0, None)
    with zf:
        infos = zf.infolist()
        members = sum(1 for i in infos if not i.filename.endswith("/"))

        def stop(code: str) -> dict:
            errors.append(code)
            return _result(errors, members, 0, None)

        seen: set = set()
        dups: set = set()
        for info in infos:
            name = info.filename
            if _unsafe(name):
                errors.append("unsafe_member_name:" + name)
            if name in seen and name not in dups:
                dups.add(name)
                errors.append("duplicate_member:" + name)
            seen.add(name)
        if errors:
            return _result(errors, members, 0, None)

        try:
            bad = zf.testzip()
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError, EOFError):
            return stop("bad_zip")
        if bad is not None:
            return stop("crc_mismatch:" + bad)

        manifest_infos = [i for i in infos
                          if i.filename == "manifest.json" or i.filename.endswith("/manifest.json")]
        if len(manifest_infos) != 1:
            return stop("manifest_count")
        manifest_name = manifest_infos[0].filename
        parts = manifest_name.split("/")
        if len(parts) != 3:
            return stop("manifest_location")
        try:
            manifest = json.loads(zf.read(manifest_infos[0]).decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            return stop("manifest_invalid")
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
            return stop("manifest_invalid")
        if manifest.get("source_id") != parts[0] or manifest.get("batch_id") != parts[1]:
            return stop("manifest_id_mismatch")
        root = parts[0] + "/" + parts[1] + "/"

        # Step 5: extraction
        data_by_name: dict = {}
        for info in infos:
            name = info.filename
            target = workdir / name
            try:
                if name.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    data = zf.read(info)
                    data_by_name[name] = data
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
            except OSError:
                continue

    # Step 6
    files = manifest["files"]
    valid: list = []
    for index, entry in enumerate(files):
        if not _valid_entry(entry):
            errors.append("invalid_file_entry:%d" % index)
            continue
        valid.append(entry)
        rel = entry["path"]
        data = data_by_name.get(root + rel)
        if data is None:
            errors.append("missing_file:" + rel)
        elif len(data) != entry["bytes"]:
            errors.append("bytes_mismatch:" + rel)
        elif hashlib.sha256(data).hexdigest() != entry["sha256"]:
            errors.append("sha256_mismatch:" + rel)

    # Step 7
    listed = {root + e["path"] for e in valid}
    for info in infos:
        name = info.filename
        if name.endswith("/") or name == manifest_name:
            continue
        if name not in listed:
            errors.append("unlisted_file:" + name)

    files_by_path = {e["path"]: e for e in valid}

    # Step 8
    normalized = [e for e in valid if e["path"].startswith("normalized/")]
    withheld = manifest.get("normalized_withheld") is True
    lines: list | None = None
    if withheld:
        if normalized:
            errors.append("normalized_not_withheld")
    elif len(normalized) != 1:
        errors.append("normalized_count")
    else:
        entry = normalized[0]
        if entry.get("format") != "jsonl":
            errors.append("normalized_format")
        else:
            data = data_by_name.get(root + entry["path"])
            if data is not None:
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    errors.append("jsonl_decode_error")
                else:
                    lines = text.split("\n")
                    if text.endswith("\n"):
                        lines = lines[:-1]
                    if text == "":
                        lines = []
                    rows = entry.get("rows")
                    if not _is_int(rows) or rows != len(lines):
                        errors.append("normalized_rows_mismatch")
    jsonl_lines = len(lines) if lines is not None else 0

    # Step 9
    counts = manifest.get("counts")
    keys = ("raw_rows", "accepted", "excluded", "rejected")
    if not isinstance(counts, dict) or not all(
            _is_int(counts.get(k)) and counts[k] >= 0 for k in keys):
        errors.append("invalid_counts")
    else:
        if lines is not None and counts["accepted"] + counts["rejected"] != len(lines):
            errors.append("jsonl_count_mismatch")
        if counts["raw_rows"] != counts["accepted"] + counts["excluded"] + counts["rejected"]:
            errors.append("raw_count_mismatch")

    # Step 10
    records = record_checker(list(lines) if lines is not None else [], manifest, files_by_path)
    if isinstance(records, dict) and records.get("ok") is False:
        errors.append("records_invalid")
    return _result(errors, members, jsonl_lines, records)

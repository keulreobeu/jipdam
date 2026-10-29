"""Keyless file downloads (lanes A1/A2/E) with a journal written before bytes are committed.

Journal schema contract.JOURNAL_SCHEMA is shared with the API page journal.
"""
from __future__ import annotations

import email.message
import hashlib
import os
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

from . import contract as C
from ._reuse import digest_file, read_json, safe_file, utc_z, write_json
from .base import RequestSpec

ContractError = C.ContractError
CHUNK = 1024 * 1024
MAGIC = {"zip": (b"PK\x03\x04",), "xlsx": (b"PK\x03\x04",), "xls": (b"\xd0\xcf\x11\xe0",)}
EXTENSIONS = {"zip": ".zip", "xlsx": ".xlsx", "xls": ".xls", "csv": ".csv", "json": ".json", "xml": ".xml"}


def new_journal(spec: RequestSpec) -> dict:
    return {"schema": C.JOURNAL_SCHEMA, "request_id": spec.request_id, "lane": spec.lane, "origin": spec.origin,
            "url_template": spec.url_template, "params": [list(p) for p in spec.params], "method": spec.method,
            "section": spec.section, "expected_kind": spec.expected_kind, "expected_rows": spec.expected_rows,
            "status": "not_collected", "error": None, "pages": [], "attempts": [], "completed_at_utc": None}


def _journal_path(batch_dir: Path, request_id: str) -> Path:
    if not C.REQUEST_ID_RE.fullmatch(request_id):
        raise ContractError("invalid_request_id")
    return safe_file(Path(batch_dir), f"raw/{request_id}/journal.json")


def recover(folder: Path, journal: dict) -> bool:
    """Promote attempts whose bytes were fully written; mark the rest interrupted."""
    changed, committed = False, {p["file"] for p in journal["pages"]}
    for item in journal["attempts"]:
        if item.get("status") != "received" or item["file"] in committed:
            continue
        final, partial = folder / item["file"], folder / (item["file"] + ".part")
        if not final.exists() and partial.exists() and digest_file(partial) == item["sha256"]:
            os.replace(partial, final)
        if final.exists():
            if digest_file(final) != item["sha256"]:
                raise ContractError("archive_integrity_failed")
            item["status"] = "success"
            journal["pages"].append({k: item[k] for k in ("page", "file", "sha256", "bytes", "http_status",
                                                           "content_type", "original_name", "retrieved_at_utc")})
            journal.update(status="complete", error=None,
                           completed_at_utc=item.get("retrieved_at_utc") or item.get("provided_at_utc"))
        else:
            item["status"] = "interrupted_write"
        changed = True
    return changed


def verify(folder: Path, journal: dict) -> None:
    for page in journal["pages"]:
        path = safe_file(folder, page["file"])
        if not path.is_file() or digest_file(path) != page["sha256"]:
            raise ContractError("archive_integrity_failed")


def _original_name(headers) -> str | None:
    raw = headers.get("Content-Disposition")
    if not raw:
        return None
    message = email.message.Message()
    message["content-disposition"] = raw
    name = message.get_filename()
    if name is None:
        return None
    try:
        name = name.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        try:
            name = name.encode("latin-1").decode("cp949")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    name = PurePosixPath(urllib.parse.unquote(name).replace("\\", "/")).name
    return name or None


def _check_head(head: bytes, kind: str) -> None:
    lowered = head[:512].lstrip().lower()
    if lowered.startswith(b"<!doctype html") or lowered.startswith(b"<html") or b"<html" in lowered[:200]:
        raise ContractError("html_instead_of_file")
    if kind in MAGIC and not head.startswith(MAGIC[kind]):
        raise ContractError("unexpected_file_type")


def _build_request(spec: RequestSpec) -> urllib.request.Request:
    if "{KEY}" in spec.url_template:
        raise ContractError("keyed_template_in_file_lane")
    url = spec.url_template
    if spec.params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(list(spec.params))
    data = urllib.parse.urlencode(list(spec.form)).encode("ascii") if spec.method == "POST" else None
    headers = {"User-Agent": C.USER_AGENT, **dict(spec.headers)}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    return urllib.request.Request(url, data=data, headers=headers, method=spec.method)


def fetch_file(spec: RequestSpec, batch_dir: Path, *, opener, clock=utc_z, sleep=time.sleep,
               max_bytes: int = C.MAX_FILE_BYTES, timeout: float = 120, retries: int = 3) -> dict:
    path = _journal_path(Path(batch_dir), spec.request_id)
    folder = path.parent
    folder.mkdir(parents=True, exist_ok=True)
    journal = read_json(path) if path.exists() else new_journal(spec)
    if recover(folder, journal):
        write_json(path, journal)
    if journal["status"] in C.BATCH_COMPLETE:
        verify(folder, journal)
        return journal
    if journal["status"] == "inconsistent":
        raise ContractError("inconsistent_request_use_new_batch")
    request = _build_request(spec)
    for retry in range(retries):
        if retry:
            sleep(2 ** retry)
        attempt = len(journal["attempts"]) + 1
        stem = f"p000001_a{attempt:06d}"
        item = {"page": 1, "attempt": attempt, "retrieved_at_utc": clock(), "status": "error"}
        partial = None
        try:
            try:
                response = opener.open(request, timeout=timeout)
            except urllib.error.HTTPError as exc:
                code = exc.code
                exc.close()
                if code in {401, 403}:
                    raise ContractError("authentication_error") from None
                raise ContractError("transient_http_error" if code == 429 or code >= 500 else "http_error") from None
            except (urllib.error.URLError, TimeoutError, OSError):
                raise ContractError("transient_transport_error") from None
            with response:
                file_name = stem + EXTENSIONS.get(spec.expected_kind, ".bin")
                partial = folder / (file_name + ".part")
                digest, size, head = hashlib.sha256(), 0, b""
                with partial.open("xb") as stream:
                    for chunk in iter(lambda: response.read(CHUNK), b""):
                        if not head:
                            head = chunk[:4096]
                        size += len(chunk)
                        if size > max_bytes:
                            raise ContractError("response_too_large")
                        digest.update(chunk)
                        stream.write(chunk)
                    stream.flush()
                    os.fsync(stream.fileno())
                item.update(file=file_name, sha256=digest.hexdigest(), bytes=size, http_status=response.status,
                            content_type=response.headers.get("Content-Type"),
                            original_name=_original_name(response.headers))
            if size == 0:
                raise ContractError("empty_download")
            _check_head(head, spec.expected_kind)
            item["status"] = "received"
            journal["attempts"].append(item)
            journal.update(status="partial", error=None)
            write_json(path, journal)  # journal the bytes before committing the final name
            os.replace(partial, folder / file_name)
            recover(folder, journal)
            write_json(path, journal)
            return journal
        except ContractError as exc:
            error = str(exc)
            if partial is not None and partial.exists():
                partial.unlink()
            item.update(status="error", error=error)
            if item not in journal["attempts"]:
                journal["attempts"].append(item)
            journal.update(error=error, status="inconsistent" if error in {"html_instead_of_file", "unexpected_file_type"}
                           else "failed")
            write_json(path, journal)
            if not error.startswith("transient_") or retry == retries - 1:
                raise
    raise ContractError("unreachable")


def ingest_provided(spec: RequestSpec, batch_dir: Path, source: Path, *, provided_at_utc: str | None = None) -> dict:
    """Inbox route when a portal needs a browser: copy (never move) the user-provided file."""
    path = _journal_path(Path(batch_dir), spec.request_id)
    folder = path.parent
    folder.mkdir(parents=True, exist_ok=True)
    journal = read_json(path) if path.exists() else new_journal(spec)
    if journal["status"] in C.BATCH_COMPLETE:
        verify(folder, journal)
        return journal
    source = Path(source)
    if not source.is_file():
        raise ContractError("provided_file_missing")
    with source.open("rb") as stream:
        _check_head(stream.read(4096), spec.expected_kind)
    attempt = len(journal["attempts"]) + 1
    file_name = f"p000001_a{attempt:06d}" + (EXTENSIONS.get(spec.expected_kind) or source.suffix.lower() or ".bin")
    target = folder / file_name
    if target.exists():
        raise ContractError("provided_target_exists")
    shutil.copyfile(source, target)
    sha = digest_file(target)
    item = {"page": 1, "attempt": attempt, "file": file_name, "sha256": sha, "bytes": target.stat().st_size,
            "http_status": None, "content_type": None, "original_name": source.name, "retrieved_at_utc": None,
            "provided_at_utc": provided_at_utc or utc_z(), "status": "received", "method": "provided"}
    journal["attempts"].append(item)
    recover(folder, journal)
    journal["pages"][-1]["provided_at_utc"] = item["provided_at_utc"]
    write_json(path, journal)
    return journal

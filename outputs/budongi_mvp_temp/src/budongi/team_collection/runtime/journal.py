"""Request journal recording every page attempt of an API or file request."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Callable

from budongi.team_collection import contract as C

_INCONSISTENT_ERROR_PREFIXES = frozenset({
    "pagination_total_changed",
    "page_row_count_mismatch",
    "pagination_metadata_mismatch",
    "html_instead_of_file",
})


class RequestJournal:
    """Multi-page request journal stored as journal.json."""

    def __init__(
        self,
        folder: Path,
        request: dict,
        *,
        clock: Callable[[], str],
        fsync: Callable[[int], None] | None = None,
    ) -> None:
        """Initialize request journal with storage folder and request spec."""
        if not isinstance(request, dict):
            raise C.ContractError("invalid_request")
        for key in ("request_id", "lane", "origin", "url_template"):
            if key not in request:
                raise C.ContractError("invalid_request")
        if request["lane"] not in C.LANES:
            raise C.ContractError("invalid_request")
        req_id = request["request_id"]
        if not isinstance(req_id, str) or not C.REQUEST_ID_RE.fullmatch(req_id):
            raise C.ContractError("invalid_request_id")

        self._folder = Path(folder)
        self._request = copy.deepcopy(request)
        self._clock = clock
        self._fsync = fsync if fsync is not None else os.fsync

    def _now(self) -> str:
        val = self._clock()
        if not isinstance(val, str) or not C.UTC_Z_RE.fullmatch(val):
            raise C.ContractError("invalid_clock")
        return val

    def _fresh_journal(self) -> dict:
        raw_params = self._request.get("params", ())
        if isinstance(raw_params, dict):
            params = [[k, v] for k, v in raw_params.items()]
        else:
            params = [list(item) for item in raw_params]
        return {
            "schema": C.JOURNAL_SCHEMA,
            "request_id": self._request["request_id"],
            "lane": self._request["lane"],
            "origin": self._request["origin"],
            "url_template": self._request["url_template"],
            "params": params,
            "method": self._request.get("method", "GET"),
            "section": self._request.get("section", ""),
            "expected_kind": self._request.get("expected_kind", "any"),
            "expected_rows": self._request.get("expected_rows", None),
            "status": "not_collected",
            "error": None,
            "pages": [],
            "attempts": [],
            "completed_at_utc": None,
        }

    def _load(self) -> dict:
        journal_file = self._folder / "journal.json"
        try:
            content = journal_file.read_text(encoding="utf-8")
            data = json.loads(content)
        except Exception:
            raise C.ContractError("journal_corrupt")
        if not isinstance(data, dict):
            raise C.ContractError("journal_corrupt")
        if data.get("schema") != C.JOURNAL_SCHEMA:
            raise C.ContractError("journal_schema_mismatch")
        for key in ("request_id", "lane", "origin", "url_template"):
            if data.get(key) != self._request[key]:
                raise C.ContractError("journal_identity_mismatch")
        return data

    def _load_or_fresh(self) -> dict:
        journal_file = self._folder / "journal.json"
        if journal_file.exists():
            return self._load()
        return self._fresh_journal()

    def _write_journal(self, data: dict) -> None:
        self._folder.mkdir(parents=True, exist_ok=True)
        tmp_path = self._folder / "journal.json.tmp"
        journal_path = self._folder / "journal.json"

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
            f.flush()
            self._fsync(f.fileno())

        for idx in range(5):
            try:
                os.replace(tmp_path, journal_path)
                break
            except PermissionError:
                if idx == 4:
                    raise

    def _match_received_attempt(self, journal: dict, attempt: object) -> dict:
        if not isinstance(attempt, dict) or "attempt" not in attempt:
            raise C.ContractError("unknown_attempt")
        attempt_num = attempt["attempt"]
        target = None
        for a in journal["attempts"]:
            if a.get("attempt") == attempt_num:
                target = a
                break
        if target is None:
            raise C.ContractError("unknown_attempt")
        if target.get("status") != "received":
            raise C.ContractError("attempt_not_received")
        return target

    def state(self) -> dict:
        """Load journal.json (creating folder and fresh journal if absent) and return a deep copy."""
        journal_file = self._folder / "journal.json"
        if journal_file.exists():
            journal = self._load()
        else:
            journal = self._fresh_journal()
            self._write_journal(journal)
        return copy.deepcopy(journal)

    def begin(self, page: int, payload: bytes, *, http_status: int, ext: str) -> dict:
        """Record a new received attempt in the journal and write the payload file."""
        journal = self._load_or_fresh()

        if journal["status"] in C.BATCH_COMPLETE:
            raise C.ContractError("journal_already_complete")
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            raise C.ContractError("invalid_page")
        if not isinstance(payload, bytes):
            raise C.ContractError("invalid_payload")
        if isinstance(http_status, bool) or not isinstance(http_status, int):
            raise C.ContractError("invalid_http_status")
        if not isinstance(ext, str) or not re.fullmatch(r"^[a-z0-9]{1,8}$", ext):
            raise C.ContractError("invalid_ext")
        if page in {p["page"] for p in journal["pages"]}:
            raise C.ContractError("page_already_committed")

        retrieved_at_utc = self._now()
        attempt_num = len(journal["attempts"]) + 1
        filename = f"p{page:06d}_a{attempt_num:06d}.{ext}"
        attempt = {
            "page": page,
            "attempt": attempt_num,
            "file": filename,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "http_status": http_status,
            "retrieved_at_utc": retrieved_at_utc,
            "status": "received",
            "error": None,
        }
        journal["attempts"].append(attempt)
        self._write_journal(journal)

        payload_path = self._folder / filename
        try:
            with open(payload_path, "xb") as f:
                f.write(payload)
                f.flush()
                self._fsync(f.fileno())
        except FileExistsError:
            raise C.ContractError("attempt_file_exists")

        return copy.deepcopy(attempt)

    def succeed(self, attempt: dict, *, rows: int, total: int | None) -> None:
        """Commit a received attempt as a page or mark journal inconsistent if total changed."""
        journal = self._load_or_fresh()

        target_attempt = self._match_received_attempt(journal, attempt)

        page = target_attempt["page"]
        if page in {p["page"] for p in journal["pages"]}:
            raise C.ContractError("page_already_committed")
        if isinstance(rows, bool) or not isinstance(rows, int) or rows < 0:
            raise C.ContractError("invalid_rows")
        if total is not None and (isinstance(total, bool) or not isinstance(total, int) or total < 0):
            raise C.ContractError("invalid_total")

        if total is not None:
            for p in journal["pages"]:
                p_total = p.get("total")
                if p_total is not None and p_total != total:
                    target_attempt["status"] = "error"
                    target_attempt["error"] = "pagination_total_changed"
                    journal["status"] = "inconsistent"
                    journal["error"] = "pagination_total_changed"
                    self._write_journal(journal)
                    raise C.ContractError("pagination_total_changed")

        target_attempt["status"] = "success"
        new_page = {
            "page": page,
            "file": target_attempt["file"],
            "sha256": target_attempt["sha256"],
            "bytes": target_attempt["bytes"],
            "rows": rows,
            "total": total,
            "http_status": target_attempt["http_status"],
            "retrieved_at_utc": target_attempt["retrieved_at_utc"],
        }
        journal["pages"].append(new_page)
        journal["pages"].sort(key=lambda p: p["page"])
        journal["status"] = "partial"
        journal["error"] = None
        self._write_journal(journal)

    def fail(self, attempt: dict | None, code: str) -> None:
        """Record an error code on the attempt and journal, setting status failed or inconsistent."""
        if not isinstance(code, str) or not code:
            raise C.ContractError("invalid_error_code")

        journal = self._load_or_fresh()
        if journal["status"] in C.BATCH_COMPLETE:
            raise C.ContractError("journal_already_complete")

        if attempt is not None:
            target = self._match_received_attempt(journal, attempt)
            target["status"] = "error"
            target["error"] = code

        prefix = code.split(":", 1)[0]
        if prefix in _INCONSISTENT_ERROR_PREFIXES:
            journal["status"] = "inconsistent"
        else:
            journal["status"] = "failed"
        journal["error"] = code
        journal["completed_at_utc"] = None
        self._write_journal(journal)

    def complete(self, *, zero: bool = False) -> None:
        """Mark the journal complete or complete_zero with completion timestamp."""
        journal = self._load_or_fresh()

        if journal["status"] in C.BATCH_COMPLETE:
            raise C.ContractError("journal_already_complete")
        if any(a.get("status") == "received" for a in journal["attempts"]):
            raise C.ContractError("journal_not_complete")
        if journal["status"] not in ("not_collected", "partial"):
            raise C.ContractError("journal_not_complete")
        if not zero and len(journal["pages"]) == 0:
            raise C.ContractError("journal_not_complete")
        if zero and any(p.get("rows", 0) != 0 for p in journal["pages"]):
            raise C.ContractError("zero_with_rows")

        journal["status"] = "complete_zero" if zero else "complete"
        journal["completed_at_utc"] = self._now()
        self._write_journal(journal)

    def recover(self, parse: Callable[[bytes], tuple[int, int | None]]) -> bool:
        """Resolve every received attempt after a crash and return whether the journal changed."""
        journal_file = self._folder / "journal.json"
        if not journal_file.exists():
            return False

        changed = False
        while True:
            journal = self._load()
            received_attempt = None
            for a in journal["attempts"]:
                if a.get("status") == "received":
                    received_attempt = a
                    break
            if received_attempt is None:
                break

            committed = {p["page"] for p in journal["pages"]}
            if received_attempt["page"] in committed:
                received_attempt["status"] = "error"
                received_attempt["error"] = "page_already_committed"
                self._write_journal(journal)
                changed = True
                continue

            file_path = self._folder / received_attempt["file"]
            if not file_path.is_file():
                received_attempt["status"] = "interrupted_write"
                self._write_journal(journal)
                changed = True
                continue

            payload = file_path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != received_attempt["sha256"]:
                raise C.ContractError("archive_integrity_failed")

            rows, total = parse(payload)
            self.succeed(received_attempt, rows=rows, total=total)
            changed = True

        return changed

    def committed_pages(self) -> set[int]:
        """Return the set of committed page numbers."""
        journal = self._load_or_fresh()
        return {p["page"] for p in journal["pages"]}

    def verify(self) -> None:
        """Check that every committed page file exists with its recorded sha256."""
        journal = self._load_or_fresh()
        for page in journal["pages"]:
            file_path = self._folder / page["file"]
            if not file_path.is_file():
                raise C.ContractError("archive_integrity_failed")
            payload = file_path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != page["sha256"]:
                raise C.ContractError("archive_integrity_failed")

"""Keyed-lane supervisor shell (L1): paced, journalled API collection for lanes B/C/D.

One request at a time per origin, paced by an injected token bucket + AIMD controller,
pre-reserved against the quota ledger, written through the request journal, parsed and
classified by injected adapter callables. No threads: daily volumes (<=1,000 calls per
service) finish comfortably at 1-3 rps, and a single writer keeps journals simple.
Every unit is injected so tests run on fakes before the outsourced units integrate.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import contract as C
from .base import RequestSpec

ContractError = C.ContractError
RETRYABLE = frozenset({"rate", "transient"})
EXTENSIONS = {"json": "json", "xml": "xml"}


@dataclass(frozen=True)
class LaneUnits:
    """Injected composition points: journal H2, quota H3, pacing E5, parse E7-E9 + classify E6."""
    journal: Callable        # (folder, request_doc) -> RequestJournal (begin/succeed/fail/complete/recover)
    bucket: Callable         # (origin) -> object with acquire() -> float
    aimd: Callable           # (origin) -> object with rate/success()/failure()
    fetch: Callable          # (spec, handle) -> {payload, http_status, content_type, retrieved_at_utc}
    parse: Callable          # (spec, payload) -> (ParsedPage, code, message)
    classify: Callable       # (spec, code, message) -> Verdict
    make_pages: Callable     # (spec, total) -> [(page_number, page_spec), ...] beyond page 1


@dataclass(frozen=True)
class LaneResult:
    request_id: str
    status: str              # contract.REQUEST_STATUSES
    pages: int
    rows: int
    error: str | None = None
    blocked_until_utc: str | None = None


def _journal_doc(spec: RequestSpec) -> dict:
    return {"schema": C.JOURNAL_SCHEMA, "request_id": spec.request_id, "lane": spec.lane,
            "origin": spec.origin, "url_template": spec.url_template,
            "params": [list(p) for p in spec.params], "method": spec.method,
            "section": spec.section, "expected_kind": spec.expected_kind,
            "expected_rows": spec.expected_rows}


def _ext(spec: RequestSpec, content_type: str | None) -> str:
    if spec.expected_kind in EXTENSIONS:
        return EXTENSIONS[spec.expected_kind]
    lowered = (content_type or "").lower()
    return "json" if "json" in lowered else "xml" if "xml" in lowered else "bin"


class LaneSupervisor:
    """Runs the requests of one keyed batch against one credential handle."""

    def __init__(self, units: LaneUnits, *, handle, quota, quota_cap: int,
                 sleep: Callable[[float], None], max_retries: int = 3,
                 pause_seconds: float = 30.0):
        self._units = units
        self._handle = handle
        self._quota = quota
        self._cap = quota_cap
        self._sleep = sleep
        self._max_retries = max_retries
        self._pause = pause_seconds

    def _call(self, spec: RequestSpec, journal, page: int):
        """One paced, quota-checked call -> ('ok'|'empty', parsed) or a stop verdict."""
        bucket, aimd = self._units.bucket(spec.origin), self._units.aimd(spec.origin)
        retries = 0
        while True:
            key_ref, bucket_name = self._handle.key_ref, spec.quota_bucket or spec.origin
            if not self._quota.reserve(key_ref, bucket_name, 1, cap=self._cap):
                return "quota_blocked", None
            bucket.acquire()
            attempt = None
            try:
                result = self._units.fetch(spec, self._handle)
            except ContractError as exc:
                self._quota.commit(key_ref, bucket_name, used=1, reserved=1)
                code = str(exc)
                if code == "authentication_error" or not code.startswith("transient_"):
                    journal.fail(None, code)
                    return "failed", None
                retries += 1
                if retries > self._max_retries:
                    journal.fail(None, code)
                    return "failed", None
                aimd.failure()
                self._sleep(self._pause)
                continue
            self._quota.commit(key_ref, bucket_name, used=1, reserved=1)
            attempt = journal.begin(page, result["payload"], http_status=result["http_status"],
                                    ext=_ext(spec, result["content_type"]))
            try:
                parsed, code, message = self._units.parse(spec, result["payload"])
            except ContractError as exc:
                journal.fail(attempt, str(exc))
                return "failed", None
            verdict = self._units.classify(spec, code, message)
            if verdict.kind in ("ok", "empty"):
                journal.succeed(attempt, rows=len(parsed.rows), total=parsed.total)
                aimd.success()
                return verdict.kind, parsed
            journal.fail(attempt, f"{verdict.kind}:{verdict.code}")
            if verdict.kind == "quota_daily":
                blocked = self._quota.block_until_reset(key_ref, bucket_name)
                return "quota_blocked", blocked
            if verdict.kind in RETRYABLE:
                retries += 1
                if retries > self._max_retries:
                    return "failed", None
                aimd.failure()
                self._sleep(self._pause)
                continue
            return "failed", None   # auth / request_error / api_response_error: never retried

    def run_request(self, spec: RequestSpec, batch_dir: Path) -> LaneResult:
        folder = Path(batch_dir) / "raw" / spec.request_id
        folder.mkdir(parents=True, exist_ok=True)
        journal = self._units.journal(folder, _journal_doc(spec))
        state = journal.state()
        if state["status"] in C.BATCH_COMPLETE:
            return LaneResult(spec.request_id, state["status"], len(state["pages"]),
                              sum(p.get("rows") or 0 for p in state["pages"]))
        if state["status"] == "inconsistent":
            return LaneResult(spec.request_id, "inconsistent", len(state["pages"]), 0,
                              error=state.get("error"))
        done = journal.committed_pages()
        if 1 in done:
            first_page = next(p for p in state["pages"] if p["page"] == 1)
            outcome, total = "ok", first_page.get("total")
        else:
            outcome, first = self._call(spec, journal, 1)
            if outcome == "quota_blocked":
                return LaneResult(spec.request_id, "not_collected", 0, 0, error="quota_blocked",
                                  blocked_until_utc=first if isinstance(first, str) else None)
            if outcome == "failed":
                state = journal.state()
                return LaneResult(spec.request_id, state["status"], len(state["pages"]), 0,
                                  error=state.get("error"))
            if outcome == "empty" and not first.rows:
                journal.complete(zero=True)
                return LaneResult(spec.request_id, "complete_zero", 1, 0)
            total = first.total
            done = journal.committed_pages()
        for page_number, page_spec in self._units.make_pages(spec, total):
            if page_number in done:
                continue
            outcome, parsed = self._call(page_spec, journal, page_number)
            if outcome == "quota_blocked":
                state = journal.state()
                return LaneResult(spec.request_id, "partial", len(state["pages"]),
                                  sum(p.get("rows") or 0 for p in state["pages"]),
                                  error="quota_blocked",
                                  blocked_until_utc=parsed if isinstance(parsed, str) else None)
            if outcome == "failed":
                state = journal.state()
                return LaneResult(spec.request_id, state["status"], len(state["pages"]),
                                  sum(p.get("rows") or 0 for p in state["pages"]),
                                  error=state.get("error"))
        state = journal.state()
        rows = sum(p.get("rows") or 0 for p in state["pages"])
        journal.complete(zero=(rows == 0))
        state = journal.state()
        return LaneResult(spec.request_id, state["status"], len(state["pages"]), rows)

    def run_batch(self, specs, batch_dir: Path) -> list[LaneResult]:
        results = []
        for spec in specs:
            result = self.run_request(spec, batch_dir)
            results.append(result)
            if result.error == "quota_blocked":
                remaining = [s for s in specs if s.request_id not in
                             {r.request_id for r in results}]
                results.extend(LaneResult(s.request_id, "not_collected", 0, 0,
                                          error="quota_blocked") for s in remaining)
                break
        return results

"""Lane supervisor: paging, quota stop, retry policy and resume (fake units, no network)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from budongi.team_collection import contract as C
from budongi.team_collection.base import ParsedPage, RequestSpec, Verdict
from budongi.team_collection.supervisor import LaneResult, LaneSupervisor, LaneUnits


def spec(request_id="r1", **overrides):
    fields = {"request_id": request_id, "lane": "B", "origin": "https://apis.data.go.kr",
              "url_template": "https://apis.data.go.kr/svc?serviceKey={KEY}",
              "credential_ref": "datagokr", "quota_bucket": "datagokr:svc"}
    fields.update(overrides)
    return RequestSpec(**fields)


class FakeJournal:
    def __init__(self, request):
        self.doc = {**request, "status": "not_collected", "error": None, "pages": [],
                    "attempts": []}

    def state(self):
        return self.doc

    def committed_pages(self):
        return {p["page"] for p in self.doc["pages"]}

    def begin(self, page, payload, *, http_status, ext):
        attempt = {"page": page, "ext": ext, "status": "received"}
        self.doc["attempts"].append(attempt)
        return attempt

    def succeed(self, attempt, *, rows, total):
        attempt["status"] = "success"
        self.doc["pages"].append({"page": attempt["page"], "rows": rows, "total": total})
        self.doc.update(status="partial", error=None)

    def fail(self, attempt, code):
        if attempt is not None:
            attempt["status"] = "error"
        self.doc.update(status="failed", error=code)

    def complete(self, *, zero=False):
        self.doc["status"] = "complete_zero" if zero else "complete"


class FakeQuota:
    def __init__(self, allow=10**9):
        self.allow, self.reserved, self.committed, self.blocked = allow, 0, 0, []

    def reserve(self, key_ref, bucket, n, *, cap):
        if self.committed + n > self.allow:
            return False
        self.reserved += n
        return True

    def commit(self, key_ref, bucket, *, used, reserved):
        self.committed += used

    def block_until_reset(self, key_ref, bucket):
        self.blocked.append(bucket)
        return "2026-10-30T15:00:00Z"


class Pace:
    def __init__(self):
        self.acquired, self.failures, self.successes = 0, 0, 0

    def acquire(self):
        self.acquired += 1
        return 0.0

    def success(self):
        self.successes += 1

    def failure(self):
        self.failures += 1


class Harness:
    """Builds a LaneSupervisor whose fetch/classify follow a script keyed by page number."""

    def __init__(self, script, total=None, rows_by_page=None, allow=10**9):
        self.script = dict(script)        # page -> "ok"|"empty"|Verdict|ContractError code
        self.total, self.rows = total, rows_by_page or {}
        self.journals, self.pace, self.quota = {}, Pace(), FakeQuota(allow)
        self.sleeps, self.calls = [], []
        handle = type("H", (), {"key_ref": "k" * 64})()
        units = LaneUnits(
            journal=lambda folder, request: self.journals.setdefault(str(folder),
                                                                     FakeJournal(request)),
            bucket=lambda origin: self.pace,
            aimd=lambda origin: self.pace,
            fetch=self.fetch,
            parse=self.parse,
            classify=self.classify,
            make_pages=lambda s, total: [(n, spec(s.request_id))
                                         for n in range(2, ((total or 0) + 9) // 10 + 1)])
        self.supervisor = LaneSupervisor(units, handle=handle, quota=self.quota, quota_cap=1000,
                                         sleep=self.sleeps.append, max_retries=2,
                                         pause_seconds=30.0)

    def _page(self):
        return len([c for c in self.calls if c == "fetch"]) and self.calls.count("fetch")

    def fetch(self, s, handle):
        self.calls.append("fetch")
        step = self.script.get(len(self.calls_pages()) + 1, "ok")
        if isinstance(step, str) and step.startswith("raise:"):
            self.script[len(self.calls_pages()) + 1] = "ok"  # next try succeeds
            raise C.ContractError(step.split(":", 1)[1])
        return {"payload": b"{}", "http_status": 200, "content_type": "application/json",
                "retrieved_at_utc": "2026-10-30T02:00:00Z"}

    def calls_pages(self):
        journal = next(iter(self.journals.values()), None)
        return journal.doc["pages"] if journal else []

    def parse(self, s, payload):
        page = len(self.calls_pages()) + 1
        rows = tuple({"n": i} for i in range(self.rows.get(page, 0)))
        return ParsedPage(rows, self.total, "ok" if rows else "empty"), "code", "msg"

    def classify(self, s, code, message):
        step = self.script.get(len(self.calls_pages()) + 1, "ok")
        if isinstance(step, Verdict):
            self.script[len(self.calls_pages()) + 1] = "ok"
            return step
        return Verdict("ok" if self.rows.get(len(self.calls_pages()) + 1) else "empty", code)


class SupervisorTests(unittest.TestCase):
    def test_multi_page_completes_and_paces_every_call(self):
        h = Harness({}, total=25, rows_by_page={1: 10, 2: 10, 3: 5})
        with tempfile.TemporaryDirectory() as tmp:
            result = h.supervisor.run_request(spec(), Path(tmp))
        self.assertEqual(result, LaneResult("r1", "complete", 3, 25))
        self.assertEqual(h.pace.acquired, 3)
        self.assertEqual(h.quota.committed, 3)

    def test_zero_result_is_complete_zero(self):
        h = Harness({}, total=0, rows_by_page={})
        with tempfile.TemporaryDirectory() as tmp:
            result = h.supervisor.run_request(spec(), Path(tmp))
        self.assertEqual((result.status, result.rows), ("complete_zero", 0))

    def test_quota_cap_stops_batch_before_any_call(self):
        h = Harness({}, total=5, rows_by_page={1: 5}, allow=0)
        with tempfile.TemporaryDirectory() as tmp:
            results = h.supervisor.run_batch([spec("r1"), spec("r2")], Path(tmp))
        self.assertEqual([(r.status, r.error) for r in results],
                         [("not_collected", "quota_blocked")] * 2)
        self.assertEqual(h.pace.acquired, 0)

    def test_daily_quota_verdict_blocks_and_reports_partial(self):
        h = Harness({2: Verdict("quota_daily", "22")}, total=25,
                    rows_by_page={1: 10, 2: 10, 3: 5})
        with tempfile.TemporaryDirectory() as tmp:
            result = h.supervisor.run_request(spec(), Path(tmp))
        self.assertEqual((result.status, result.error), ("partial", "quota_blocked"))
        self.assertEqual(result.blocked_until_utc, "2026-10-30T15:00:00Z")
        self.assertEqual(h.quota.blocked, ["datagokr:svc"])

    def test_transient_retries_then_succeeds_auth_never_retries(self):
        h = Harness({1: "raise:transient_http_error"}, total=5, rows_by_page={1: 5})
        with tempfile.TemporaryDirectory() as tmp:
            result = h.supervisor.run_request(spec(), Path(tmp))
        self.assertEqual(result.status, "complete")
        self.assertEqual(h.pace.failures, 1)
        self.assertEqual(h.sleeps, [30.0])
        h2 = Harness({1: "raise:authentication_error"}, total=5, rows_by_page={1: 5})
        with tempfile.TemporaryDirectory() as tmp:
            result = h2.supervisor.run_request(spec(), Path(tmp))
        self.assertEqual((result.status, result.error), ("failed", "authentication_error"))
        self.assertEqual(h2.sleeps, [])

    def test_resume_skips_committed_pages(self):
        h = Harness({}, total=25, rows_by_page={1: 10, 2: 10, 3: 5})
        with tempfile.TemporaryDirectory() as tmp:
            folder = str(Path(tmp) / "raw" / "r1")
            journal = h.journals.setdefault(folder, FakeJournal({"request_id": "r1"}))
            journal.doc.update(status="partial")
            journal.doc["pages"].append({"page": 1, "rows": 10, "total": 25})
            result = h.supervisor.run_request(spec(), Path(tmp))
        self.assertEqual(result.status, "complete")
        self.assertEqual(h.pace.acquired, 2)   # only pages 2 and 3 were fetched

    def test_completed_journal_is_not_refetched(self):
        h = Harness({}, total=5, rows_by_page={1: 5})
        with tempfile.TemporaryDirectory() as tmp:
            folder = str(Path(tmp) / "raw" / "r1")
            journal = h.journals.setdefault(folder, FakeJournal({"request_id": "r1"}))
            journal.doc.update(status="complete")
            journal.doc["pages"].append({"page": 1, "rows": 5, "total": 5})
            result = h.supervisor.run_request(spec(), Path(tmp))
        self.assertEqual((result.status, h.pace.acquired), ("complete", 0))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from budongi.team_collection import contract as C
from budongi.team_collection.runtime.journal import RequestJournal

REQ = {"request_id": "bus-001", "lane": "B", "origin": "https://api.example",
       "url_template": "https://api.example/{KEY}/x", "params": (("page", "1"),)}


class _Clock:
    def __init__(self) -> None:
        self.n = 0

    def __call__(self) -> str:
        self.n += 1
        return f"2026-10-29T03:00:{self.n:02d}Z"


class JournalVisibleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.folder = Path(self._tmp.name) / "raw" / "bus-001"
        self.fsyncs: list = []
        self.j = RequestJournal(self.folder, REQ, clock=_Clock(), fsync=self.fsyncs.append)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_state_creates_fresh_journal(self) -> None:
        s = self.j.state()
        self.assertEqual(s["schema"], C.JOURNAL_SCHEMA)
        self.assertEqual(len(s), 15)
        self.assertEqual(s["params"], [["page", "1"]])
        self.assertEqual((s["status"], s["pages"], s["attempts"]), ("not_collected", [], []))
        self.assertTrue((self.folder / "journal.json").is_file())

    def test_begin_records_attempt_and_writes_payload(self) -> None:
        a = self.j.begin(1, b"{}", http_status=200, ext="json")
        self.assertEqual(a["file"], "p000001_a000001.json")
        self.assertEqual((a["page"], a["attempt"], a["bytes"]), (1, 1, 2))
        self.assertEqual(a["sha256"], hashlib.sha256(b"{}").hexdigest())
        self.assertEqual((a["status"], a["error"]), ("received", None))
        self.assertEqual((self.folder / a["file"]).read_bytes(), b"{}")
        on_disk = json.loads((self.folder / "journal.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["attempts"][0]["status"], "received")
        self.assertEqual(len(self.fsyncs), 2)

    def test_succeed_commits_page(self) -> None:
        a = self.j.begin(1, b"abc", http_status=200, ext="xml")
        self.assertIsNone(self.j.succeed(a, rows=10, total=25))
        s = self.j.state()
        self.assertEqual(s["status"], "partial")
        self.assertEqual(s["attempts"][0]["status"], "success")
        self.assertEqual((s["pages"][0]["rows"], s["pages"][0]["total"]), (10, 25))
        self.assertEqual(self.j.committed_pages(), {1})

    def test_total_change_is_inconsistent(self) -> None:
        self.j.succeed(self.j.begin(1, b"a", http_status=200, ext="json"), rows=10, total=25)
        b = self.j.begin(2, b"b", http_status=200, ext="json")
        with self.assertRaises(C.ContractError) as cm:
            self.j.succeed(b, rows=10, total=26)
        self.assertEqual(str(cm.exception), "pagination_total_changed")
        self.assertEqual(self.j.state()["status"], "inconsistent")

    def test_fail_sets_failed_or_inconsistent(self) -> None:
        self.j.fail(None, "transient_http")
        self.assertEqual(self.j.state()["status"], "failed")
        self.j.fail(None, "page_row_count_mismatch:3")
        s = self.j.state()
        self.assertEqual((s["status"], s["error"]), ("inconsistent", "page_row_count_mismatch:3"))

    def test_complete_and_complete_zero(self) -> None:
        self.j.succeed(self.j.begin(1, b"a", http_status=200, ext="json"), rows=1, total=1)
        self.j.complete()
        s = self.j.state()
        self.assertEqual(s["status"], "complete")
        self.assertRegex(s["completed_at_utc"], C.UTC_Z_RE)
        other = RequestJournal(Path(self._tmp.name) / "z", REQ, clock=_Clock(), fsync=lambda fd: None)
        other.complete(zero=True)
        self.assertEqual(other.state()["status"], "complete_zero")

    def test_recover_commits_received_attempt(self) -> None:
        self.j.begin(1, b"payload", http_status=200, ext="json")
        fresh = RequestJournal(self.folder, REQ, clock=_Clock(), fsync=lambda fd: None)
        self.assertIs(fresh.recover(lambda data: (len(data), 7)), True)
        self.assertEqual(fresh.state()["pages"][0]["rows"], 7)
        self.assertIs(fresh.recover(lambda data: (0, None)), False)

    def test_verify_passes_for_intact_pages(self) -> None:
        self.j.succeed(self.j.begin(1, b"a", http_status=200, ext="json"), rows=1, total=None)
        self.assertIsNone(self.j.verify())


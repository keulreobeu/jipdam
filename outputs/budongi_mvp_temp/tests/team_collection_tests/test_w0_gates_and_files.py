"""W0 lead shells: registry gates, immutable plans and the keyless file journal (no network)."""
from __future__ import annotations

import copy
import email.message
import hashlib
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from budongi.team_collection import cli
from budongi.team_collection import contract as C
from budongi.team_collection.filefetch import fetch_file, ingest_provided, recover
from budongi.team_collection.registry import (check_fetch_gate, make_plan, spec_from_plan, validate_registry,
                                              write_plan)

RECORD = "https://github.com/keulreobeu/jipdam/issues/42"


def registry() -> dict:
    return {
        "schema_version": C.REGISTRY_SCHEMA, "approval_ref": "2026-10-29 test approval",
        "http_key_exposure_ack": {"ref": "test ack", "origins": ["http://openapi.seoul.go.kr:8088"]},
        "sources": [
            {"t_id": "T001", "source_id": "kric_station", "dataset_id": "15013205", "status": "approved",
             "lane": "A1", "record_type": "facility", "license": {"class": "unrestricted", "ref": "x"},
             "origin_allowlist": ["https://example.test"],
             "requests": [{"request_id": "f001", "url_template": "https://example.test/file.xlsx",
                           "expected_kind": "xlsx", "section": "sheet"}]},
            {"t_id": "T003", "source_id": "seoul_station_master", "dataset_id": "OA-21232", "status": "approved",
             "lane": "D", "record_type": "facility", "license": {"class": "kogl1", "ref": "x"},
             "origin_allowlist": ["http://openapi.seoul.go.kr:8088"],
             "requests": [{"request_id": "w0001",
                           "url_template": "http://openapi.seoul.go.kr:8088/{KEY}/json/subwayStationMaster/1/1000/"}]},
            {"t_id": "T099", "source_id": "pending_source", "dataset_id": "x", "status": "pending", "lane": "A1",
             "record_type": "facility", "license": {"class": "unknown", "ref": "x"},
             "origin_allowlist": ["https://example.test"], "requests": []},
        ],
    }


class FakeResponse(io.BytesIO):
    def __init__(self, payload: bytes, *, status=200, disposition=None, ctype="application/octet-stream"):
        super().__init__(payload)
        self.status = status
        self.headers = email.message.Message()
        self.headers["Content-Type"] = ctype
        if disposition:
            self.headers["Content-Disposition"] = disposition


class FakeOpener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = 0

    def open(self, request, timeout=None):
        self.calls += 1
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def no_network():
    return FakeOpener(AssertionError("network must not be used"))


XLSX = b"PK\x03\x04" + b"x" * 2000


class RegistryGateTests(unittest.TestCase):
    def test_registry_rejects_bad_shapes(self):
        cases = []
        bad = registry(); bad["schema_version"] = "other"; cases.append(("unsupported_registry", bad))
        bad = registry(); bad["sources"][1]["t_id"] = "T001"; cases.append(("duplicate_source", bad))
        bad = registry(); bad["sources"][0]["requests"][0]["url_template"] = "https://evil.test/x"
        cases.append(("origin_not_allowlisted", bad))
        bad = registry(); bad["sources"][0]["requests"][0]["url_template"] = "https://example.test/{KEY}/x"
        cases.append(("keyed_template_in_file_lane", bad))
        for code, value in cases:
            with self.subTest(code=code), self.assertRaises(C.ContractError) as caught:
                validate_registry(value)
            self.assertEqual(str(caught.exception), code)

    def test_plan_requires_approval_batch_id_and_record_url(self):
        reg = registry()
        validate_registry(reg)
        for kwargs, code in [({"key": "T099", "batch_id": "a-20261029-v1", "record_url": RECORD}, "source_not_approved"),
                             ({"key": "T001", "batch_id": "Bad_ID", "record_url": RECORD}, "invalid_batch_id"),
                             ({"key": "T001", "batch_id": "a-20261029-v1", "record_url": "https://x.test/1"},
                              "invalid_record_url")]:
            key = kwargs.pop("key")
            with self.subTest(code=code), self.assertRaises(C.ContractError) as caught:
                make_plan(reg, key, **kwargs)
            self.assertEqual(str(caught.exception), code)
        plan = make_plan(reg, "T001", batch_id="kric-station-20261029-v1", record_url=RECORD)
        self.assertEqual(plan["requests"][0]["request_id"], "f001")
        self.assertEqual(plan["quality_status"], C.QUALITY_STATUS)

    def test_fetch_gate_needs_record_and_http_acknowledgement(self):
        reg = registry()
        plan = make_plan(reg, "T003", batch_id="seoul-station-20261029-v1", record_url=RECORD)
        self.assertEqual(check_fetch_gate(reg, plan)["t_id"], "T003")
        missing = dict(plan, record_url="")
        with self.assertRaisesRegex(C.ContractError, "github_collection_record_required"):
            check_fetch_gate(reg, missing)
        unacknowledged = copy.deepcopy(reg)
        unacknowledged["http_key_exposure_ack"] = {}
        with self.assertRaisesRegex(C.ContractError, "http_key_not_acknowledged"):
            check_fetch_gate(unacknowledged, plan)

    def test_plans_are_immutable(self):
        reg = registry()
        with tempfile.TemporaryDirectory() as tmp:
            plan = make_plan(reg, "T001", batch_id="kric-station-20261029-v1", record_url=RECORD,
                             created_at_utc="2026-10-29T00:00:00Z")
            write_plan(Path(tmp), plan)
            self.assertEqual(write_plan(Path(tmp), dict(plan, created_at_utc="2026-10-30T00:00:00Z"))["batch_id"],
                             plan["batch_id"])
            with self.assertRaisesRegex(C.ContractError, "existing_plan_differs_use_new_batch"):
                write_plan(Path(tmp), dict(plan, record_url=RECORD.replace("42", "43")))


class FileJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        plan = make_plan(registry(), "T001", batch_id="kric-station-20261029-v1", record_url=RECORD)
        self.spec = spec_from_plan(plan["requests"][0])

    def tearDown(self):
        self.tmp.cleanup()

    def test_download_is_journaled_and_not_refetched(self):
        disposition = "attachment; filename*=UTF-8''%EC%97%AD%EC%82%AC.xlsx"
        opener = FakeOpener(FakeResponse(XLSX, disposition=disposition))
        journal = fetch_file(self.spec, self.dir, opener=opener, sleep=lambda _: None)
        self.assertEqual(journal["status"], "complete")
        page = journal["pages"][0]
        self.assertEqual(page["sha256"], hashlib.sha256(XLSX).hexdigest())
        self.assertEqual(page["original_name"], "역사.xlsx")
        self.assertTrue((self.dir / "raw" / "f001" / page["file"]).is_file())
        again = fetch_file(self.spec, self.dir, opener=no_network(), sleep=lambda _: None)
        self.assertEqual(again["pages"][0]["sha256"], page["sha256"])

    def test_html_instead_of_file_is_inconsistent_and_not_kept(self):
        opener = FakeOpener(FakeResponse(b"<!DOCTYPE html><html><body>login</body></html>", ctype="text/html"))
        with self.assertRaisesRegex(C.ContractError, "html_instead_of_file"):
            fetch_file(self.spec, self.dir, opener=opener, sleep=lambda _: None)
        journal = json.loads((self.dir / "raw" / "f001" / "journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["status"], "inconsistent")
        self.assertEqual(journal["pages"], [])
        self.assertEqual([p.name for p in (self.dir / "raw" / "f001").iterdir()], ["journal.json"])

    def test_transient_error_retries_and_auth_error_does_not(self):
        transient = urllib.error.HTTPError("u", 503, "busy", None, io.BytesIO())
        opener = FakeOpener(transient, FakeResponse(XLSX))
        journal = fetch_file(self.spec, self.dir, opener=opener, sleep=lambda _: None)
        self.assertEqual((opener.calls, journal["status"]), (2, "complete"))
        other = Path(self.tmp.name) / "other"
        auth = FakeOpener(urllib.error.HTTPError("u", 401, "no", None, io.BytesIO()), FakeResponse(XLSX))
        with self.assertRaisesRegex(C.ContractError, "authentication_error"):
            fetch_file(self.spec, other, opener=auth, sleep=lambda _: None)
        self.assertEqual(auth.calls, 1)

    def test_crash_between_journal_and_rename_is_recovered(self):
        folder = self.dir / "raw" / "f001"
        folder.mkdir(parents=True)
        (folder / "p000001_a000001.xlsx.part").write_bytes(XLSX)
        journal = {"schema": C.JOURNAL_SCHEMA, "request_id": "f001", "status": "partial", "error": None, "pages": [],
                   "attempts": [{"page": 1, "attempt": 1, "file": "p000001_a000001.xlsx",
                                 "sha256": hashlib.sha256(XLSX).hexdigest(), "bytes": len(XLSX), "http_status": 200,
                                 "content_type": None, "original_name": None,
                                 "retrieved_at_utc": "2026-10-29T00:00:00Z", "status": "received"}]}
        self.assertTrue(recover(folder, journal))
        self.assertEqual(journal["status"], "complete")
        self.assertTrue((folder / "p000001_a000001.xlsx").is_file())

    def test_provided_file_is_copied_not_moved(self):
        source = self.dir / "inbox.xlsx"
        source.write_bytes(XLSX)
        journal = ingest_provided(self.spec, self.dir / "batch", source, provided_at_utc="2026-10-29T01:02:03Z")
        self.assertEqual(journal["status"], "complete")
        self.assertTrue(source.exists())
        self.assertEqual(journal["pages"][0]["provided_at_utc"], "2026-10-29T01:02:03Z")


class CliLockTests(unittest.TestCase):
    def test_live_lock_blocks_and_stale_lock_is_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / ".fetch.lock").write_text(str(os.getpid()), encoding="ascii")
            with self.assertRaisesRegex(C.ContractError, "collection_in_use"):
                cli._lock(folder)
            with mock.patch.object(cli, "process_alive", return_value=False):
                path = cli._lock(folder)
            self.assertEqual(path.read_text(encoding="ascii"), str(os.getpid()))

    def test_cli_plan_then_fetch_then_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "reg.json"
            reg_path.write_text(json.dumps(registry()), encoding="utf-8")
            data_root = Path(tmp) / "data"
            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                code = cli.main(["--registry", str(reg_path), "plan", "--source", "T001", "--batch-id",
                                 "kric-station-20261029-v1", "--record-url", RECORD, "--data-root", str(data_root)])
            self.assertEqual(code, 0)
            batch = Path(json.loads(out.getvalue())["batch_dir"])
            with mock.patch.object(cli, "file_opener", return_value=FakeOpener(FakeResponse(XLSX))), \
                    mock.patch("sys.stdout", io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
                code = cli.main(["--registry", str(reg_path), "fetch-files", "--batch-dir", str(batch)])
            self.assertEqual(code, 0)
            self.assertFalse((batch / ".fetch.lock").exists())
            status = cli.batch_status(batch)
            self.assertTrue(status["complete"])


if __name__ == "__main__":
    unittest.main()

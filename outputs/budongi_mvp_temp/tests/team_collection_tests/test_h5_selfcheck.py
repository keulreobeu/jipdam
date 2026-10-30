from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from budongi.team_collection.contract import ContractError
from budongi.team_collection.package.selfcheck import check_zip

ROOT = "s1/b-20261029-v1/"
JSONL = b'{"a":1}\n{"a":2}\n'
CSV = b"id,name\n1,x\n"


def entry(path, data, fmt, rows=None):
    e = {"path": path, "format": fmt, "bytes": len(data),
         "sha256": hashlib.sha256(data).hexdigest()}
    if rows is not None:
        e["rows"] = rows
    return e


def manifest(**over):
    m = {"source_id": "s1", "batch_id": "b-20261029-v1",
         "files": [entry("raw/a.csv", CSV, "csv"),
                   entry("normalized/facility.jsonl", JSONL, "jsonl", 2)],
         "counts": {"raw_rows": 3, "accepted": 2, "excluded": 1, "rejected": 0}}
    m.update(over)
    return m


class _Checker:
    def __init__(self):
        self.calls = []

    def __call__(self, lines, man, files):
        self.calls.append((list(lines), man, files))
        return {"ok": True, "n": 7}


class SelfCheckVisibleTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.base = Path(self._tmp.name)
        self.zip = self.base / "pkg.zip"
        self.work = self.base / "work"
        self.checker = _Checker()

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, man, extra=()):
        with zipfile.ZipFile(self.zip, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr(ROOT + "manifest.json", json.dumps(man))
            zf.writestr(ROOT + "raw/a.csv", CSV)
            zf.writestr(ROOT + "normalized/facility.jsonl", JSONL)
            for name, data in extra:
                zf.writestr(name, data)

    def run_check(self):
        return check_zip(self.zip, workdir=self.work, record_checker=self.checker)

    def test_valid_package_passes(self):
        man = manifest()
        self.write(man)
        res = self.run_check()
        self.assertEqual(res, {"ok": True, "errors": [],
                               "counts": {"members": 3, "jsonl_lines": 2},
                               "records": {"ok": True, "n": 7}})
        self.assertEqual(len(self.checker.calls), 1)
        lines, got_man, files = self.checker.calls[0]
        self.assertEqual(lines, ['{"a":1}', '{"a":2}'])
        self.assertEqual(got_man, man)
        self.assertEqual(files["raw/a.csv"], man["files"][0])
        self.assertEqual((self.work / ROOT / "raw/a.csv").read_bytes(), CSV)

    def test_sha_mismatch_is_reported(self):
        man = manifest()
        man["files"][0]["sha256"] = "0" * 64
        self.write(man)
        res = self.run_check()
        self.assertFalse(res["ok"])
        self.assertEqual(res["errors"], ["sha256_mismatch:raw/a.csv"])
        self.assertEqual(len(self.checker.calls), 1)

    def test_unlisted_file_is_reported(self):
        self.write(manifest(), extra=[(ROOT + "README.md", b"hi")])
        res = self.run_check()
        self.assertEqual(res["errors"], ["unlisted_file:" + ROOT + "README.md"])
        self.assertEqual(res["counts"]["members"], 4)

    def test_non_empty_workdir_raises(self):
        self.write(manifest())
        self.work.mkdir()
        (self.work / "x.txt").write_text("x")
        with self.assertRaises(ContractError) as ctx:
            self.run_check()
        self.assertEqual(str(ctx.exception), "workdir_not_empty")

    def test_not_a_zip_is_bad_zip(self):
        self.zip.write_bytes(b"not a zip")
        res = self.run_check()
        self.assertEqual(res, {"ok": False, "errors": ["bad_zip"],
                               "counts": {"members": 0, "jsonl_lines": 0},
                               "records": None})
        self.assertEqual(self.checker.calls, [])


if __name__ == "__main__":
    unittest.main()


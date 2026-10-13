"""Statistics provenance, vintage and rejection contracts using synthetic cells."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from openpyxl import Workbook

from budongi.statistics_storage import StatisticsError, import_statistics, statistics_status


class StatisticsStorageTests(unittest.TestCase):
    def setUp(self):
        runtime = Path(__file__).resolve().parents[3] / ".local_runtime"
        runtime.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="statistics-test-", dir=runtime)
        self.root = Path(self.temporary.name)
        self.db = self.root / "stats" / "statistics.sqlite3"

    def tearDown(self):
        self.temporary.cleanup()

    def workbook(self, name, rows, folder="inputs"):
        path = self.root / folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        book = Workbook()
        book.active.title = "Synthetic statistics"
        for row in rows:
            book.active.append(row)
        book.save(path)
        return path

    def query(self, sql, args=()):
        with closing(sqlite3.connect(self.db)) as db:
            return db.execute(sql, args).fetchall()

    def test_exact_source_cells_missing_zero_and_raw_archive(self):
        path = self.workbook("아파트 매매평균가격.xlsx", [
            ["지역명", "2026-08-01 09:00:52", "2026-09-01 09:00:52"],
            ["서울", 12345.678901, "-"], ["전국", 0, None]])
        before = path.read_bytes()
        result = import_statistics(self.db, "synthetic_first", [path])
        self.assertEqual(4, result["new_observations"])
        self.assertEqual(2, result["files"][0]["missing_cells"])
        self.assertEqual(before, path.read_bytes())
        archive = self.db.parent / result["files"][0]["archive_path"]
        self.assertEqual(before, archive.read_bytes())
        records = self.query("SELECT source_row,source_column,period_key,value_status,value_decimal FROM stat_observations ORDER BY source_row,source_column")
        self.assertEqual((2, 2, "2026-08", "numeric", "12345.678901"), records[0])
        self.assertEqual("0", records[2][-1])
        self.assertEqual(0, statistics_status(self.db)["foreign_key_violations"])
        self.assertEqual("ok", statistics_status(self.db)["integrity_check"])

    def test_pir_monthly_quintiles_and_raw_time_are_not_quarterly(self):
        path = self.workbook("PIR.xlsx", [["지역", "주택분위", "소득분위", "2026-06-01 09:00:52"],
                                         ["서울", 5, 1, 42.1], ["서울", 1, 5, 1.2]])
        import_statistics(self.db, "synthetic_pir", [path])
        dims = [json.loads(r[0]) for r in self.query("SELECT dimensions_json FROM series")]
        self.assertEqual({1, 5}, {r["주택분위"] for r in dims})
        self.assertEqual({("2026-06", "2026-06-01 09:00:52")}, set(self.query("SELECT period_key,source_header_raw FROM stat_observations")))

    def test_replay_new_batch_and_revised_history_preserve_previous_values(self):
        rows = [["지역명", "2026-09-01 09:00:52"], ["서울", 100]]
        first = self.workbook("월간 아파트 매매가격지수_20261013.xlsx", rows)
        import_statistics(self.db, "synthetic_v1", [first])
        digest = hashlib.sha256(self.db.read_bytes()).hexdigest()
        replay = import_statistics(self.db, "synthetic_v1", [first])
        self.assertEqual(0, replay["new_observations"])
        self.assertEqual(digest, hashlib.sha256(self.db.read_bytes()).hexdigest())
        manifest = self.db.parent / "manifests/synthetic_v1.json"
        original_manifest = manifest.read_bytes()
        tampered = json.loads(original_manifest)
        tampered["batch_cells"] = 999
        manifest.write_text(json.dumps(tampered), encoding="utf-8")
        with self.assertRaises(StatisticsError):
            import_statistics(self.db, "synthetic_v1", [first])
        manifest.write_bytes(original_manifest)
        reused = import_statistics(self.db, "synthetic_v2", [first])
        self.assertEqual(0, reused["new_observations"])
        revised = self.workbook("월간 아파트 매매가격지수_20261014.xlsx",
                                [rows[0], ["서울", 101]], folder="revised")
        import_statistics(self.db, "synthetic_v3", [revised])
        self.assertEqual([(100.0,), (101.0,)], self.query("SELECT value_numeric FROM stat_observations ORDER BY value_numeric"))
        self.assertEqual([(101.0,)], self.query("SELECT value_numeric FROM latest_stat_observations"))
        before = self.db.read_bytes()
        with self.assertRaises(StatisticsError):
            import_statistics(self.db, "synthetic_v1", [revised])
        self.assertEqual(before, self.db.read_bytes())

    def test_region_context_and_rounded_dashboard_are_separate_series(self):
        full = self.workbook("미등록.xlsx", [])  # unregistered input must never enter a batch
        with self.assertRaises(StatisticsError):
            import_statistics(self.db, "synthetic_unknown", [full])
        self.assertFalse(self.db.exists())
        full = self.workbook("월간 아파트 매매가격지수_20261013.xlsx",
                             [["지역명", "2026-09-01 09:00:52"], ["서울", 100], ["중구", 100],
                              ["부산", 100], ["중구", 101]])
        detailed = self.workbook("월간 매수우위지수.xlsx",
                                 [["지역", "구분", "2026-09-01 09:00:52"], ["서울", "매수우위지수", 71.234]])
        rounded = self.workbook("서울 월간 매수 우위 지수.xlsx",
                                [["조사항목", "2026-09-01 09:00:52"], ["매수우위지수", 71.2]])
        import_statistics(self.db, "synthetic_context", [full, detailed, rounded])
        contexts = [json.loads(r[0])["원천상위지역"] for r in self.query(
            "SELECT dimensions_json FROM series WHERE dimensions_json LIKE '%중구%'")]
        self.assertEqual({"서울", "부산"}, set(contexts))
        self.assertEqual(6, len(self.query("SELECT * FROM latest_stat_observations")))

    def test_invalid_cells_and_layout_roll_back_all_batch_members(self):
        valid = self.workbook("아파트 매매평균가격.xlsx", [["지역명", "2026-09-01 09:00:52"], ["서울", 10]])
        import_statistics(self.db, "synthetic_valid", [valid])
        invalid_rows = [
            [["지역명", "2026-09-01 09:00:52"], ["서울", "=1+1"]],
            [["지역명", "2026-09-01 09:00:52"], ["서울", True]],
            [["지역명", "2026-09-01 09:00:52"], ["서울", "not a value"]],
            [["지역명", "2026-09-01 09:00:52", "2026-09-02 09:00:52"], ["서울", 1, 2]],
            [["지역명", "2026-09-01 09:00:52"], [None, 1]],
        ]
        for index, rows in enumerate(invalid_rows):
            with self.subTest(index=index):
                invalid = self.workbook("아파트 전세평균가격.xlsx", rows)
                counts = self.query("SELECT count(*) FROM import_batches")
                with self.assertRaises(StatisticsError):
                    import_statistics(self.db, f"synthetic_bad_{index}", [valid, invalid])
                self.assertEqual(counts, self.query("SELECT count(*) FROM import_batches"))
                self.assertEqual([(1,)], self.query("SELECT count(*) FROM stat_observations"))

    def test_wrong_db_and_source_archive_tampering_are_rejected(self):
        self.db.parent.mkdir()
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("CREATE TABLE transactions(id INTEGER)")
            db.commit()
        before = self.db.read_bytes()
        path = self.workbook("아파트 매매평균가격.xlsx", [["지역명", "2026-09-01 09:00:52"], ["서울", 10]])
        with self.assertRaises(StatisticsError):
            import_statistics(self.db, "synthetic_other_db", [path])
        self.assertEqual(before, self.db.read_bytes())
        second_db = self.root / "second" / "statistics.sqlite3"
        result = import_statistics(second_db, "synthetic_archive", [path])
        archive = second_db.parent / result["files"][0]["archive_path"]
        archive.write_bytes(b"tampered")
        with self.assertRaises(StatisticsError):
            import_statistics(second_db, "synthetic_archive", [path])

    def test_cli_import_list_and_readonly_status_leave_historical_db_absent(self):
        path = self.workbook("아파트 매매평균가격.xlsx", [["지역명", "2026-09-01 09:00:52"], ["서울", 10]])
        manifest = self.root / "inputs.json"
        manifest.write_text(json.dumps([str(path)]), encoding="utf-8")
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
        prefix = [sys.executable, "-X", "utf8", "-m", "budongi.cli", "statistics"]
        result = subprocess.run(prefix + ["import", "--statistics-db", str(self.db), "--batch-id", "synthetic_cli",
                                         "--input-list", str(manifest)], cwd=self.root, env=env, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(1, json.loads(result.stdout)["new_observations"])
        result = subprocess.run(prefix + ["status", "--statistics-db", str(self.db)], cwd=self.root,
                                env=env, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("ok", json.loads(result.stdout)["integrity_check"])
        self.assertFalse((self.root / "data/historical/serving.sqlite3").exists())

    def test_audit_rounding_overlap_and_evidence_do_not_modify_source_observations(self):
        from budongi.statistics_audit import audit_statistics, record_audit_reviews
        first = self.workbook("월간 매수우위지수.xlsx", [["지역", "구분", "2026-09-01 09:00:52"],
                                                      ["서울", "매수우위지수", 71.23456]])
        second = self.workbook("서울 월간 매수 우위 지수.xlsx", [["조사항목", "2026-09-01 09:00:52"],
                                                             ["매수우위지수", 71.2]])
        import_statistics(self.db, "synthetic_overlap", [first,second])
        report = audit_statistics(self.db, [first,second])
        self.assertEqual(2, report["total_cells"])
        self.assertTrue(report["duplicate_pairs"][0]["rounded_duplicate"])
        self.assertEqual(1, record_audit_reviews(self.db,report))
        self.assertEqual(0, record_audit_reviews(self.db,report))
        self.assertEqual([(2,)], self.query("SELECT count(*) FROM stat_observations"))
        archive = self.db.parent / statistics_status(self.db)["files"][0]["archive_path"]
        archive.write_bytes(b"bad")
        with self.assertRaises(StatisticsError):
            audit_statistics(self.db)


if __name__ == "__main__":
    unittest.main()

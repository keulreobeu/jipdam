import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from budongi.rental_candidate_export import CandidateExportError, export_rental_candidates


class RentalCandidateExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".local_runtime").mkdir()
        self.database = self.root / "canonical.sqlite3"
        connection = sqlite3.connect(self.database)
        connection.executescript("""
            CREATE TABLE complexes(complex_id TEXT PRIMARY KEY, identifier_namespace TEXT, source_complex_id TEXT);
            CREATE TABLE observations(
                observation_id TEXT PRIMARY KEY, complex_id TEXT, kind TEXT, sgg_cd TEXT,
                legal_dong TEXT, jibun TEXT, apartment_name TEXT, contract_date TEXT,
                source_id TEXT, area_sqm REAL, deposit_krw INTEGER, monthly_rent_krw INTEGER,
                normalized_payload_json TEXT
            );
            CREATE TABLE match_candidates(
                batch_id TEXT, observation_id TEXT, complex_id TEXT,
                supporting_observation_id TEXT, review_status TEXT, confidence TEXT,
                confidence_score REAL, match_basis TEXT
            );
            INSERT INTO complexes VALUES ('c1','namespace','official-1'),('c2','namespace','official-2');
            INSERT INTO observations VALUES
                ('official-support-1','c1','sale','11110','가동','1-1','Alpha','2025-01-01','official-source',50,NULL,NULL,'{}'),
                ('official-support-2','c2','sale','11110','가동','1-1','Alpha','2025-01-01','official-source',50,NULL,NULL,'{}'),
                ('r1',NULL,'jeonse','11110','가동','1-1','Alpha','2025-03-01','rental-source',40,100000000,0,'{"secret":"raw"}'),
                ('r2',NULL,'jeonse','11110','가동','1-1','Alpha','2025-04-01','rental-source',45,90000000,0,'{}'),
                ('w1',NULL,'wolse','11110','가동','1-1','Alpha','2025-05-01','rental-source',35,50000000,50,'{}'),
                ('s1',NULL,'sale','11110','가동','1-1','Alpha','2025-06-01','sale-source',50,NULL,NULL,'{}');
            INSERT INTO match_candidates VALUES
                ('b1','r1','c1','official-support-1','pending','unverified',NULL,'exact labels'),
                ('b2','r1','c1','official-support-1','pending','unverified',NULL,'exact labels'),
                ('b1','r1','c2','official-support-2','pending','unverified',NULL,'exact labels'),
                ('b1','r2','c1','official-support-1','pending','unverified',NULL,'exact labels'),
                ('b1','w1','c1','official-support-1','pending','unverified',NULL,'exact labels'),
                ('b1','s1','c1','official-support-1','pending','unverified',NULL,'exact labels');
        """)
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp.cleanup()

    def test_exports_distinct_pending_rental_pairs_and_ambiguous_groups_read_only(self):
        before = self.database.read_bytes()
        output = self.root / ".local_runtime" / "review-1"
        result = export_rental_candidates(self.database, output, project_root=self.root)
        self.assertEqual(result["status"], "exported_review_reference_only")
        self.assertEqual(result["candidate_pair_rows"], 4)
        self.assertEqual(result["candidate_group_rows"], 3)
        self.assertEqual(result["ambiguous_groups"], 1)
        self.assertFalse(result["importable_review_package"])
        self.assertEqual(before, self.database.read_bytes())
        self.assertEqual({p.name for p in output.iterdir()}, {"README.txt", "candidate_pairs.csv", "candidate_groups.csv"})
        with (output / "candidate_pairs.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["kind"] for row in rows}, {"jeonse", "wolse"})
        self.assertTrue(all(row["review_status"] == "pending" and row["confidence"] == "unverified" for row in rows))
        self.assertTrue(all(row["supporting_observation_ids"] for row in rows))
        self.assertEqual(next(row for row in rows if row["observation_id"] == "r1" and row["candidate_complex_id"] == "c1")["candidate_link_rows"], "2")
        self.assertNotIn("secret", (output / "candidate_pairs.csv").read_text(encoding="utf-8-sig"))
        self.assertNotIn("100000000", (output / "candidate_pairs.csv").read_text(encoding="utf-8-sig"))
        with (output / "candidate_groups.csv").open(encoding="utf-8-sig", newline="") as stream:
            groups = list(csv.DictReader(stream))
        self.assertEqual(sum(row["ambiguous"] == "yes" for row in groups), 2)
        self.assertIn("rental_review_v1", (output / "README.txt").read_text(encoding="utf-8"))

    def test_formula_prefixes_are_neutralized(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("create table sample(value text)")
        connection.execute("insert into sample values (?)", ("  =1+1",))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            from budongi.rental_candidate_export import _write_csv
            _write_csv(path, ("value",), connection.execute("select value from sample"))
            with path.open(encoding="utf-8-sig", newline="") as stream:
                self.assertEqual(list(csv.DictReader(stream))[0]["value"], "'  =1+1")

    def test_rejects_existing_or_non_local_output_without_modifying_it(self):
        existing = self.root / ".local_runtime" / "already-there"
        existing.mkdir()
        marker = existing / "keep.txt"
        marker.write_text("keep", encoding="utf-8")
        with self.assertRaises(CandidateExportError):
            export_rental_candidates(self.database, existing, project_root=self.root)
        with self.assertRaises(CandidateExportError):
            export_rental_candidates(self.database, self.root / "outside", project_root=self.root)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()

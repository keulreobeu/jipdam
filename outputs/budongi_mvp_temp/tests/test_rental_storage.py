from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from budongi.public_data import PublicDataError, parse_molit_rental_response
from budongi.rental_storage import connect_rental, import_rental_snapshot, observation_id_for


class RentalDataContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = connect_rental(self.root / "data" / "rental.sqlite3")
        self.addCleanup(self.db.close)
        self.page_hash = "a" * 64
        self.source_file = "11110/202510/page_0001.xml"
        self.manifest = {"datasets": [{
            "source": "molit_apt_rent",
            "retrieved_at_utc": "2026-10-06T01:00:00Z",
            "files": [{"path": self.source_file, "sha256": self.page_hash, "rows": 2}],
        }]}

    def observation(self, row_number: int = 1) -> dict[str, object]:
        key = observation_id_for(source="molit_apt_rent", source_file_ref=self.source_file,
                                 source_content_sha256=self.page_hash,
                                 source_row_number=row_number)
        return {
            "observation_id": key,
            "source": "molit_apt_rent",
            "source_record_id": None,
            "source_file_ref": self.source_file,
            "source_content_sha256": self.page_hash,
            "source_row_number": row_number,
            "sgg_cd": "11110",
            "legal_dong": "청운동",
            "apartment_name": "합성 단지",
            "jibun": "1-1",
            "contract_date": "2025-10-11",
            "rental_type": "jeonse",
            "deposit_krw": 350_000_000,
            "monthly_rent_krw": 0,
            "area_sqm": 59.96,
            "floor": 4,
            "build_year": 2017,
            "contract_term": None,
            "contract_type": None,
            "renewal_right_used": None,
            "previous_deposit_krw": None,
            "previous_monthly_rent_krw": None,
            "source_status": None,
            "raw_payload": {"fixtureName": "합성 단지", "fixtureAmount": "35000"},
        }

    def test_xml_reader_preserves_source_fields_and_does_not_invent_state(self) -> None:
        payload = (b"<response><header><resultCode>000</resultCode></header>"
                   b"<body><items><item><fixtureName>Fixture</fixtureName><fixtureAmount>35000</fixtureAmount>"
                   b"<fixtureBlank> </fixtureBlank>"
                   b"</item></items><totalCount>1</totalCount></body></response>")
        rows, total = parse_molit_rental_response(payload)
        self.assertEqual(total, 1)
        self.assertEqual(rows[0]["fixtureAmount"], "35000")
        self.assertEqual(rows[0]["fixtureBlank"], " ")
        self.assertNotIn("transactionId", rows[0])
        self.assertNotIn("cancelStatus", rows[0])
        with self.assertRaises(PublicDataError):
            parse_molit_rental_response(b"not xml")

    def test_snapshot_keeps_equal_rows_distinct_and_unknown_status_null(self) -> None:
        second = self.observation(row_number=2)
        result = import_rental_snapshot(
            self.db, snapshot_id="rental-fixture-v1", snapshot_date="2026-10-06",
            source_manifest=self.manifest,
            observations=[self.observation(), second],
        )
        self.assertEqual(result["observations"], 2)
        rows = self.db.execute(
            "SELECT observation_id, source_record_id, source_status, deposit_krw, monthly_rent_krw "
            "FROM rental_observations ORDER BY source_row_number"
        ).fetchall()
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(rows[0]["observation_id"], rows[1]["observation_id"])
        self.assertIsNone(rows[0]["source_record_id"])
        self.assertIsNone(rows[0]["source_status"])
        self.assertEqual((rows[0]["deposit_krw"], rows[0]["monthly_rent_krw"]),
                         (350_000_000, 0))
        self.assertEqual(self.db.execute(
            "SELECT sealed FROM rental_snapshots WHERE snapshot_id = 'rental-fixture-v1'"
        ).fetchone()[0], 1)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "UNIQUE constraint failed"):
            import_rental_snapshot(
                self.db, snapshot_id="rental-fixture-v1", snapshot_date="2026-10-06",
                source_manifest=self.manifest, observations=[self.observation()],
            )
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM rental_observations").fetchone()[0], 2)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "snapshots are immutable"):
            self.db.execute(
                "UPDATE rental_observations SET deposit_krw = 1 "
                "WHERE snapshot_id = 'rental-fixture-v1'"
            )
        with self.assertRaisesRegex(sqlite3.IntegrityError, "snapshots are immutable"):
            self.db.execute("DELETE FROM rental_snapshots WHERE snapshot_id = 'rental-fixture-v1'")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "snapshots are immutable"):
            self.db.execute(
                "INSERT INTO rental_observations SELECT * FROM rental_observations "
                "WHERE snapshot_id = 'rental-fixture-v1' LIMIT 1"
            )
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM rental_observations").fetchone()[0], 2)

    def test_complexes_facilities_and_unknown_coverage_keep_separate_provenance(self) -> None:
        complex_hash, facility_hash, coverage_hash = "b" * 64, "c" * 64, "d" * 64
        datasets = []
        for source, path, digest, rows in [
            ("molit_apt_rent", self.source_file, self.page_hash, 1),
            ("synthetic_complex_catalog", "fixture/complexes.csv", complex_hash, 1),
            ("synthetic_facility_catalog", "fixture/facilities.csv", facility_hash, 1),
            ("synthetic_coverage_report", "fixture/coverage.csv", coverage_hash, 1),
        ]:
            datasets.append({"source": source, "retrieved_at_utc": "2026-10-06T01:00:00Z",
                             "files": [{"path": path, "sha256": digest, "rows": rows}]})
        complex_row = {
            "complex_id": "APT_FIXTURE_A", "name": "합성 단지", "sgg_cd": "11110",
            "legal_dong": "청운동", "jibun": "1-1", "latitude": 37.59, "longitude": 126.97,
            "identity_evidence": "fixture-only reviewed key", "source": "synthetic_complex_catalog",
            "source_file_ref": "fixture/complexes.csv", "source_content_sha256": complex_hash,
            "source_row_number": 1, "raw_payload": {"id": "fixture"},
        }
        facility_row = {
            "source": "synthetic_facility_catalog", "source_file_ref": "fixture/facilities.csv",
            "source_content_sha256": facility_hash, "source_row_number": 1,
            "facility_observation_id": observation_id_for(
                source="synthetic_facility_catalog", source_file_ref="fixture/facilities.csv",
                source_content_sha256=facility_hash, source_row_number=1),
            "source_facility_id": "SYNTHETIC_STATION_01", "category": "station",
            "name": "가상역", "sgg_cd": "11110", "latitude": 37.591,
            "longitude": 126.971, "raw_payload": {"id": "fixture"},
        }
        coverage_row = {
            "source": "synthetic_coverage_report", "source_file_ref": "fixture/coverage.csv",
            "source_content_sha256": coverage_hash, "source_row_number": 1,
            "category": "hospital", "sgg_cd": "11110", "coverage_status": "unknown",
            "covered_feature_count": None, "checked_at_utc": "2026-10-06T01:00:00Z",
            "raw_payload": {"coverage": "not measured"},
        }
        result = import_rental_snapshot(
            self.db, snapshot_id="rental-geo-fixture", snapshot_date="2026-10-06",
            source_manifest={"datasets": datasets}, observations=[self.observation()],
            complexes=[complex_row], facilities=[facility_row], coverage=[coverage_row],
        )
        self.assertEqual((result["complexes"], result["facilities"], result["coverage"]), (1, 1, 1))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM rental_observation_matches").fetchone()[0], 0)
        state = self.db.execute(
            "SELECT coverage_status, covered_feature_count FROM rental_facility_coverage"
        ).fetchone()
        self.assertEqual((state["coverage_status"], state["covered_feature_count"]), ("unknown", None))

    def test_bad_row_rolls_back_snapshot_and_confirmed_match_needs_review_evidence(self) -> None:
        invalid = self.observation()
        invalid["contract_date"] = "2027-01-01"
        with self.assertRaisesRegex(ValueError, "exceeds rental snapshot_date"):
            import_rental_snapshot(
                self.db, snapshot_id="rollback", snapshot_date="2026-10-06",
                source_manifest=self.manifest, observations=[self.observation(), invalid],
            )
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM rental_snapshots").fetchone()[0], 0)

        digest = "b" * 64
        complex_row = {
            "complex_id": "APT_FIXTURE", "name": "합성 단지", "sgg_cd": "11110",
            "identity_evidence": "fixture", "source": "synthetic_complex_catalog",
            "source_file_ref": "fixture/complexes.csv", "source_content_sha256": digest,
            "source_row_number": 1, "raw_payload": {},
        }
        datasets = [*self.manifest["datasets"], {
            "source": "synthetic_complex_catalog", "retrieved_at_utc": "2026-10-06T01:00:00Z",
            "files": [{"path": "fixture/complexes.csv", "sha256": digest, "rows": 1}],
        }]
        key = self.observation()["observation_id"]
        with self.assertRaisesRegex(ValueError, "require evidence and reviewer"):
            import_rental_snapshot(
                self.db, snapshot_id="bad-match", snapshot_date="2026-10-06",
                source_manifest={"datasets": datasets}, observations=[self.observation()],
                complexes=[complex_row], matches=[{
                    "observation_id": key, "complex_id": "APT_FIXTURE",
                    "review_status": "confirmed", "match_basis": "name only",
                }],
            )
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM rental_snapshots").fetchone()[0], 0)

    def test_manifest_rejects_credentials_and_historical_database_is_not_extended(self) -> None:
        with self.assertRaisesRegex(ValueError, "Credentials are forbidden"):
            import_rental_snapshot(
                self.db, snapshot_id="secret", snapshot_date="2026-10-06",
                source_manifest={"datasets": [{**self.manifest["datasets"][0], "service_key": "do-not-store"}]},
                observations=[],
            )
        with self.assertRaisesRegex(ValueError, "Credentials are forbidden"):
            import_rental_snapshot(
                self.db, snapshot_id="secret-raw", snapshot_date="2026-10-06",
                source_manifest=self.manifest,
                observations=[{**self.observation(), "raw_payload": {"access_token": "do-not-store"}}],
            )
        historical = self.root / "serving.sqlite3"
        connection = sqlite3.connect(historical)
        with connection:
            connection.execute("CREATE TABLE transactions (id TEXT)")
        connection.close()
        with self.assertRaisesRegex(ValueError, "Refusing to mix"):
            connect_rental(historical)
        connection = sqlite3.connect(historical)
        with connection:
            names = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        connection.close()
        self.assertEqual(names, {"transactions"})

    def test_observation_must_match_manifest_file_hash_and_row_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match a source manifest file"):
            import_rental_snapshot(
                self.db, snapshot_id="hash-mismatch", snapshot_date="2026-10-06",
                source_manifest=self.manifest,
                observations=[{**self.observation(), "source_content_sha256": "f" * 64}],
            )
        with self.assertRaisesRegex(ValueError, "exceeds the manifest row count"):
            import_rental_snapshot(
                self.db, snapshot_id="row-overflow", snapshot_date="2026-10-06",
                source_manifest=self.manifest,
                observations=[self.observation(row_number=3)],
            )
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM rental_snapshots").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()

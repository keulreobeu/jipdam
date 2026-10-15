"""Synthetic-only snapshot_date boundary tests; no canonical database required."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from budongi.rental_recommendation import RentalDataUnavailable
from budongi.rental_review import file_sha256, load_review_package


class LoadReviewPackageSnapshotDateTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="synthetic-rental-review-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

        records_path = self.root / "synthetic_records.json"
        self.records = {
            "relations": [],
            "coordinates": [],
            "facilities": [],
            "coverage": [],
        }
        records_path.write_text(json.dumps(self.records), encoding="utf-8")

        # A synthetic file digest serves as the source identity; no DB is used.
        self.source_hash = file_sha256(records_path)
        self.manifest = {
            "schema_version": "rental_review_v1",
            "source_db_sha256": self.source_hash,
            "quality_status": "synthetic_only",
            "approval_ref": "synthetic-test-approval-not-real",
            "approved_by": "synthetic-test-operator-not-real",
            # This instant is 2025-01-02 00:00 in Seoul.
            "approved_at_utc": "2025-01-01T15:00:00Z",
            "records_file": records_path.name,
            "files": [
                {
                    "path": records_path.name,
                    "sha256": file_sha256(records_path),
                }
            ],
        }

    def write_manifest(self):
        (self.root / "manifest.json").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )

    def load(self, *, allow_synthetic=True):
        self.write_manifest()
        return load_review_package(
            self.root, self.source_hash, allow_synthetic=allow_synthetic
        )

    def test_cutoff_uses_seoul_approval_calendar_day(self):
        for cutoff, accepted in (
            ("2025-01-01", True),
            ("2025-01-02", True),
            ("2025-01-03", False),
        ):
            with self.subTest(snapshot_date=cutoff):
                self.manifest["snapshot_date"] = cutoff
                if accepted:
                    result = self.load()
                    self.assertEqual(result["manifest"]["snapshot_date"], cutoff)
                    for category, rows in self.records.items():
                        self.assertEqual(result[category], rows)
                else:
                    with self.assertRaises(RentalDataUnavailable):
                        self.load()

    def test_timezone_naive_approval_is_rejected(self):
        self.manifest["snapshot_date"] = "2025-01-02"
        for approved_at in (
            "2025-01-01T15:00:00",
            "2025-01-02T00:00:00",
        ):
            with self.subTest(approved_at_utc=approved_at):
                self.manifest["approved_at_utc"] = approved_at
                with self.assertRaises(RentalDataUnavailable):
                    self.load()

    def test_invalid_noncanonical_and_nonstring_cutoffs_are_rejected(self):
        for cutoff in (
            "",
            "not-a-date",
            "2025-02-30",
            "2025-1-2",
            "20250102",
            "2025-W01-4",
            "2025-01-02T00:00:00",
            " 2025-01-02",
            "2025-01-02 ",
            20250102,
        ):
            with self.subTest(snapshot_date=cutoff):
                self.manifest["snapshot_date"] = cutoff
                with self.assertRaises(RentalDataUnavailable):
                    self.load()

    def test_snapshot_date_can_be_omitted(self):
        result = self.load()
        self.assertNotIn("snapshot_date", result["manifest"])
        self.assertEqual(result["manifest"]["quality_status"], "synthetic_only")

    def test_synthetic_package_requires_explicit_opt_in(self):
        self.write_manifest()
        with self.subTest(allow_synthetic="omitted"):
            with self.assertRaises(RentalDataUnavailable):
                load_review_package(self.root, self.source_hash)
        with self.subTest(allow_synthetic=False):
            with self.assertRaises(RentalDataUnavailable):
                self.load(allow_synthetic=False)
        with self.subTest(allow_synthetic=True):
            result = self.load(allow_synthetic=True)
            self.assertEqual(result["manifest"]["quality_status"], "synthetic_only")


if __name__ == "__main__":
    unittest.main()

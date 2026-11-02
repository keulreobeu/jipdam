"""Frozen, parent-owned BENCH-FACILITY-001 acceptance. Synthetic packages only.

This file is committed before implementation and is outside the CLI worker's
write scope. It is readable; it is not presented as a hidden evaluator.
"""
from copy import deepcopy
import csv
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False), encoding="utf-8")


class FacilityAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.serial = 0
        self.validate = importlib.import_module("budongi.team_package").validate_package

    def fixture(self, statuses=("accepted", "excluded", "rejected"), normalized_format="jsonl"):
        self.serial += 1
        root = self.base / ("package-" + str(self.serial))
        (root / "raw").mkdir(parents=True)
        (root / "normalized").mkdir()
        stream = io.StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(["name", "code"])
        for i in range(len(statuses)):
            writer.writerow(["가상 시설\n분관" if i == 0 else "가상 시설" + str(i), "001"])
        raw = root / "raw/facilities.csv"
        raw.write_bytes(stream.getvalue().encode("utf-8"))
        records = [{"record_type": "facility", "name": "가상 시설" + str(i), "facility_type_code": "001",
                    "entity_level": "facility", "source_file_ref": "raw/facilities.csv", "source_content_sha256": sha(raw),
                    "source_section": "records", "source_row_number": i + 1, "validation_status": status,
                    "validation_reason": None if status == "accepted" else "synthetic_source_rule",
                    "latitude": None, "longitude": None} for i, status in enumerate(statuses)]
        manifest = {"delivery_schema_version": "team_collection_v1", "source_id": "synthetic_facility",
                    "dataset_id": "fixture", "provider": "synthetic", "documentation_url": "https://example.invalid/docs",
                    "batch_id": "fixture-v1", "mapping_version": "v1", "collector": "synthetic-owner",
                    "record_url": "https://example.invalid/reservation", "approval_ref": "synthetic_fixture_only",
                    "license_ref": "fixture-only", "license_review_status": "pending",
                    "scope": {"regions": ["synthetic"], "period": None, "filters": {}},
                    "source_retrieved_at_utc": None, "provided_at_utc": None, "staged_at_utc": None,
                    "quality_status": "synthetic_only", "files": [], "missing_fields": [], "errors": [], "source_missing_dates": [],
                    "requests": [{"collection_status": "complete_zero" if not statuses else "complete",
                                  "expected_rows": len(statuses), "received_rows": len(statuses)}],
                    "counts": {"raw": len(statuses), **{s: statuses.count(s) for s in ("accepted", "excluded", "rejected")}}}
        self.file_entry(root, manifest, "raw/facilities.csv", "csv", len(statuses))
        self.write_records(root, manifest, records, normalized_format)
        dump(root / "manifest.json", manifest)
        return root, manifest, records

    def file_entry(self, root, manifest, name, kind, rows):
        path = root / name
        entry = {"path": name, "format": kind, "bytes": path.stat().st_size, "sha256": sha(path), "section": "records", "rows": rows}
        old = next((f for f in manifest["files"] if f["path"] == name), None)
        if old: old.update(entry)
        else: manifest["files"].append(entry)

    def write_records(self, root, manifest, records, kind="jsonl"):
        name = "normalized/facility." + kind
        if kind == "jsonl":
            (root / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
        else:
            stream = io.StringIO(newline="")
            columns = list(records[0]) if records else ["name", "facility_type_code", "entity_level", "validation_status"]
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader(); writer.writerows(records)
            (root / name).write_bytes(stream.getvalue().encode("utf-8"))
        self.file_entry(root, manifest, name, kind, len(records))
        dump(root / "manifest.json", manifest)

    def report(self, root):
        result = self.validate(root)
        self.assertEqual(set(result), {"schema_version", "record_type", "valid", "counts", "errors"})
        self.assertEqual(result["schema_version"], "team_collection_validation_v1")
        self.assertEqual(result["record_type"], "facility")
        self.assertIs(type(result["valid"]), bool)
        self.assertIsInstance(result["errors"], list)
        for error in result["errors"]:
            self.assertEqual(set(error), {"file", "row", "field", "reason"})
            self.assertIsInstance(error["file"], str)
            self.assertFalse(Path(error["file"]).is_absolute())
            self.assertTrue(error["row"] is None or type(error["row"]) is int and error["row"] > 0)
        return result

    def error(self, report, field, reason=None, row=None):
        self.assertFalse(report["valid"])
        found = [e for e in report["errors"] if field in e["field"] and (reason is None or e["reason"] == reason)
                 and (row is None or e["row"] == row)]
        self.assertTrue(found, (field, reason, row, report["errors"]))

    def test_valid_jsonl_counts_are_not_double_counted(self):
        root, manifest, _ = self.fixture()
        result = self.report(root)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["counts"], manifest["counts"])
        self.assertEqual(result["errors"], [])

    def test_valid_csv_preserves_codes_and_quoted_newline_rows(self):
        root, manifest, _ = self.fixture(normalized_format="csv")
        result = self.report(root)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["counts"], manifest["counts"])

    def test_explicit_zero_and_nullable_metadata(self):
        root, _, _ = self.fixture(statuses=())
        result = self.report(root)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["counts"], dict(raw=0, accepted=0, excluded=0, rejected=0))

    def test_each_required_manifest_group(self):
        for field in ("source_id", "dataset_id", "provider", "documentation_url", "batch_id", "mapping_version",
                      "collector", "record_url", "approval_ref", "license_review_status", "scope", "requests",
                      "source_retrieved_at_utc", "provided_at_utc", "staged_at_utc", "quality_status", "files", "counts",
                      "missing_fields", "errors", "source_missing_dates"):
            with self.subTest(field=field):
                root, manifest, _ = self.fixture(); del manifest[field]
                dump(root / "manifest.json", manifest)
                self.error(self.report(root), field, "required")

    def test_bad_manifest_types_version_and_unknown_dates(self):
        for field, value in (("delivery_schema_version", "other-v9"), ("source_id", None), ("source_id", " "),
                             ("files", {}), ("counts", []), ("source_retrieved_at_utc", "2026-02-30T00:00:00Z"),
                             ("provided_at_utc", "2026-01-01T00:00:00"), ("quality_status", "verified")):
            with self.subTest(field=field, value=value):
                root, manifest, _ = self.fixture(); manifest[field] = value
                dump(root / "manifest.json", manifest)
                self.error(self.report(root), field)

    def test_license_pending_and_valid_date_are_not_quality_promotion(self):
        root, manifest, _ = self.fixture()
        manifest.update(source_retrieved_at_utc="2026-01-01T00:00:00Z", snapshot_date="2026-01-01")
        dump(root / "manifest.json", manifest)
        result = self.report(root)
        self.assertTrue(result["valid"], result)
        self.assertNotIn("recommendation_ready", result)
        self.assertEqual(json.loads((root / "manifest.json").read_text(encoding="utf-8"))["license_review_status"], "pending")

    def test_file_hash_bytes_and_rows_are_independently_compared(self):
        for key, value, reason in (("sha256", "0" * 64, "sha256_mismatch"), ("bytes", 999999, "bytes_mismatch"),
                                   ("rows", 999999, "rows_mismatch")):
            with self.subTest(key=key):
                root, manifest, _ = self.fixture(); manifest["files"][0][key] = value
                dump(root / "manifest.json", manifest)
                self.error(self.report(root), key, reason)

    def test_missing_file_duplicate_and_escape_are_not_read(self):
        for path, reason in (("../outside.csv", "unsafe_path"), ("/absolute.csv", "unsafe_path"),
                             ("C:/outside.csv", "unsafe_path"), ("raw/../outside.csv", "unsafe_path"),
                             ("raw\\outside.csv", "unsafe_path"), ("raw/missing.csv", "file_missing")):
            with self.subTest(path=path):
                root, manifest, _ = self.fixture(); manifest["files"][0]["path"] = path
                dump(root / "manifest.json", manifest)
                result = self.report(root)
                self.assertTrue(any(e["reason"] == reason for e in result["errors"]), result)
        root, manifest, _ = self.fixture(); manifest["files"].append(deepcopy(manifest["files"][0]))
        dump(root / "manifest.json", manifest)
        self.assertFalse(self.report(root)["valid"])

    def test_facility_required_fields_and_source_codes(self):
        for field, value in (("name", ""), ("facility_type_code", None), ("entity_level", "complex")):
            with self.subTest(field=field):
                root, manifest, records = self.fixture(); records[1][field] = value
                self.write_records(root, manifest, records)
                self.error(self.report(root), field, row=2)
        root, manifest, records = self.fixture()
        records[0]["facility_type_code"] = "unmapped-school-001"
        self.write_records(root, manifest, records)
        self.assertTrue(self.report(root)["valid"])

    def test_envelope_inheritance_and_explicit_identity_conflicts(self):
        root, manifest, records = self.fixture()
        for record in records:
            del record["source_section"]; del record["record_type"]
        dump(root / "schema.json", {"defaults": {"source_section": "records", "record_type": "facility"}})
        self.file_entry(root, manifest, "schema.json", "json", None)
        self.write_records(root, manifest, records)
        self.assertTrue(self.report(root)["valid"])
        for field, value in (("source_id", "different"), ("batch_id", "other"), ("mapping_version", "other"),
                             ("source_id", None), ("source_id", False)):
            with self.subTest(field=field, value=value):
                root, manifest, records = self.fixture(); records[0][field] = value
                self.write_records(root, manifest, records)
                self.error(self.report(root), field, row=1)

    def test_provenance_and_strict_row_types(self):
        for field, value in (("source_file_ref", "raw/unknown.csv"), ("source_content_sha256", "f" * 64),
                             ("source_row_number", 0), ("source_row_number", True), ("source_row_number", 1.5),
                             ("source_section", "")):
            with self.subTest(field=field, value=value):
                root, manifest, records = self.fixture(); records[0][field] = value
                self.write_records(root, manifest, records)
                self.error(self.report(root), field, row=1)

    def test_status_and_reason_are_not_silently_reclassified(self):
        for field, value, row in (("validation_status", "unknown", 0), ("validation_reason", None, 1),
                                 ("validation_reason", "", 2)):
            with self.subTest(field=field, value=value):
                root, manifest, records = self.fixture(); records[row][field] = value
                self.write_records(root, manifest, records)
                self.error(self.report(root), field, row=row + 1)

    def test_count_equations_and_boolean_counts(self):
        for key, value in (("raw", 6), ("accepted", 2), ("excluded", 2), ("rejected", 0), ("raw", True), ("accepted", -1)):
            with self.subTest(key=key, value=value):
                root, manifest, _ = self.fixture(); manifest["counts"][key] = value
                dump(root / "manifest.json", manifest)
                self.error(self.report(root), key)

    def test_optional_namespace_and_coordinates_remain_optional_but_paired(self):
        for update in ({"source_entity_id": "0001"}, {"latitude": 37.5}, {"latitude": True, "longitude": 127.0},
                       {"latitude": 91, "longitude": 127.0}, {"latitude": 37.5, "longitude": 181}):
            with self.subTest(update=update):
                root, manifest, records = self.fixture(); records[0].update(update)
                self.write_records(root, manifest, records)
                self.assertFalse(self.report(root)["valid"])
        root, manifest, records = self.fixture()
        records[0].update(source_entity_id="0001", identifier_namespace="synthetic:facility", latitude=37.5, longitude=127.0)
        self.write_records(root, manifest, records)
        self.assertTrue(self.report(root)["valid"])

    def test_malformed_json_and_record_location(self):
        root, _, _ = self.fixture()
        (root / "manifest.json").write_text("{bad", encoding="utf-8")
        self.assertTrue(any(e["reason"] == "invalid_json" for e in self.report(root)["errors"]))
        root, manifest, _ = self.fixture()
        p = root / "normalized/facility.jsonl"; lines = p.read_text(encoding="utf-8").splitlines()
        p.write_text(lines[0] + "\n{bad\n" + lines[2] + "\n", encoding="utf-8")
        self.file_entry(root, manifest, "normalized/facility.jsonl", "jsonl", 3)
        dump(root / "manifest.json", manifest)
        result = self.report(root)
        self.assertTrue(any(e["reason"] == "invalid_json" and e["row"] == 2 for e in result["errors"]), result)

    def test_repeated_equal_values_are_distinct_rows(self):
        root, manifest, records = self.fixture(statuses=("accepted", "accepted"))
        records[1]["name"] = records[0]["name"]
        self.write_records(root, manifest, records)
        result = self.report(root)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["counts"]["accepted"], 2)

    def test_validation_only_rejections_are_unsupported_in_this_profile(self):
        root, manifest, records = self.fixture()
        self.write_records(root, manifest, records[:2])
        dump(root / "validation.json", {"rejected": [{"source_file_ref": "raw/facilities.csv",
             "source_row_number": 3, "reason": "synthetic_source_rule"}]})
        self.file_entry(root, manifest, "validation.json", "json", None)
        dump(root / "manifest.json", manifest)
        result = self.report(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any(e["reason"] == "unsupported_layout" for e in result["errors"]), result)
        self.assertNotEqual(result["counts"]["rejected"], 0)

    def test_deterministic_errors_no_writes_or_sensitive_values(self):
        root, manifest, records = self.fixture()
        marker = "SYNTHETIC-MUST-NOT-REFLECT"
        manifest["documentation_url"] = "https://example.invalid/docs?serviceKey=" + marker
        records[1]["name"] = ""
        self.write_records(root, manifest, records)
        before = {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}
        one, two = self.report(root), self.report(root)
        self.assertEqual(one, two)
        self.assertEqual(before, {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()})
        self.assertNotIn(marker, json.dumps(one))
        self.assertNotIn(str(root), json.dumps(one))
        self.assertEqual(one["errors"], sorted(one["errors"], key=lambda e: (e["file"], e["row"] or 0, e["field"], e["reason"])))

    def test_cli_matches_api_and_exit_code(self):
        root, manifest, _ = self.fixture()
        environment = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        for valid in (True, False):
            if not valid:
                manifest["counts"]["raw"] = 99; dump(root / "manifest.json", manifest)
            result = subprocess.run([sys.executable, "-X", "utf8", "-m", "budongi.team_package", str(root)],
                                    capture_output=True, text=True, encoding="utf-8", env=environment, timeout=20)
            self.assertEqual(result.returncode, 0 if valid else 2, result.stderr)
            self.assertEqual(json.loads(result.stdout), self.report(root))


if __name__ == "__main__":
    unittest.main()

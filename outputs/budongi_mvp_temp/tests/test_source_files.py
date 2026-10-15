"""Registered file adapter contracts use explicitly fictional source fixtures."""
import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from budongi.collection import CollectionError, digest_file, read_json, write_json
from budongi.source_files import stage_file


class FileSourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = {"source_id": "fictional_file_source", "format": "csv", "status": "approved",
                       "scope": "isolated fictional fixture", "approval_ref": "unit test fixture only",
                       "fictional": True, "mapping_version": "fixture_mapping_v1", "expected_rows": 2,
                       "field_mapping": {"date": {"column": "date", "type": "date", "required": True},
                                         "amount": {"column": "amount", "type": "amount_krw", "unit": "manwon", "required": True},
                                         "label": {"column": "label", "required": True}}}
        self.registry = self.root / "registry.json"

    def register(self):
        write_json(self.registry, {"schema_version": "source_registry_v1", "sources": [self.source]})

    def rows(self):
        return [{"date": "2026-09-15", "amount": "1,234", "label": "같은 값"}] * 2

    def csv(self, rows=None):
        path = self.root / "input.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["date", "amount", "label"])
            writer.writeheader()
            writer.writerows(self.rows() if rows is None else rows)
        return path

    def stage(self, path, name="stage"):
        self.register()
        return stage_file(registry_path=self.registry, source_id=self.source["source_id"], input_path=path, output=self.root / name)

    def test_csv_raw_rows_exact_amount_reuse_and_sealed_stage(self):
        original = self.csv()
        result = self.stage(original)
        self.assertEqual(result["counts"], {"valid": 2, "rejected": 0})
        self.assertTrue(result["complete"])
        self.assertEqual(digest_file(original), result["raw_sha256"])
        self.assertEqual(result["quality_status"], "synthetic")
        c = sqlite3.connect(self.root / "stage/staging.sqlite3")
        try:
            rows = c.execute("SELECT observation_id,standard_json FROM staging_items ORDER BY row_position").fetchall()
            self.assertNotEqual(rows[0][0], rows[1][0])
            self.assertEqual(json.loads(rows[0][1])["amount"], 12340000)
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("DELETE FROM staging_items")
        finally:
            c.close()
        data = read_json(self.registry)
        data["sources"].append({"source_id": "unrelated", "status": "draft"})
        write_json(self.registry, data)
        reused = stage_file(registry_path=self.registry, source_id=self.source["source_id"], input_path=original, output=self.root / "stage")
        self.assertTrue(reused["reused"])

    def test_json_nested_unknown_raw_values_and_explicit_field_path_are_preserved(self):
        self.source["format"] = "json"
        self.source["items_path"] = ["data", "rows"]
        self.source["field_mapping"]["label"]["column"] = ["nested", "label"]
        records = self.rows()
        records = [r | {"nested": {"label": r["label"]}, "unknown": [{"future": True}, None]} for r in records]
        path = self.root / "input.json"
        path.write_text(json.dumps({"data": {"rows": records}, "other": "preserved in raw file"}), encoding="utf-8")
        self.stage(path)
        c = sqlite3.connect(self.root / "stage/staging.sqlite3")
        try:
            raw = json.loads(c.execute("SELECT raw_json FROM staging_items LIMIT 1").fetchone()[0])
            self.assertEqual(raw["unknown"], [{"future": True}, None])
        finally:
            c.close()

    def test_xlsx_all_sheets_including_empty_sections_and_equal_rows_are_distinct(self):
        from openpyxl import Workbook
        self.source["format"] = "xlsx"
        self.source["sheets"] = ["서울A", "서울B", "빈시트"]
        self.source["expected_rows_by_section"] = {"서울A": 1, "서울B": 1, "빈시트": 0}
        book = Workbook()
        book.remove(book.active)
        for name in self.source["sheets"]:
            sheet = book.create_sheet(name)
            if name != "빈시트":
                sheet.append(["date", "amount", "label"])
                sheet.append(list(self.rows()[0].values()))
        path = self.root / "input.xlsx"
        book.save(path)
        book.close()
        result = self.stage(path)
        self.assertTrue(result["complete"])
        self.assertEqual(result["sections"], self.source["expected_rows_by_section"])
        c = sqlite3.connect(self.root / "stage/staging.sqlite3")
        try:
            self.assertEqual(c.execute("SELECT COUNT(DISTINCT observation_id) FROM staging_items").fetchone()[0], 2)
        finally:
            c.close()
        self.source["sheets"] = ["서울A"]
        with self.assertRaisesRegex(CollectionError, "all_workbook_sheets"):
            self.stage(path, "bad-sheet")

    def test_strict_date_number_and_blank_required_values_leave_rejected_row_reasons(self):
        self.source["expected_rows"] = 3
        rows = [self.rows()[0] | {"date": "2026-09-15ignored"},
                self.rows()[0] | {"amount": "1,2,3"}, self.rows()[0] | {"label": "   "}]
        result = self.stage(self.csv(rows))
        self.assertEqual(result["counts"], {"valid": 0, "rejected": 3})
        self.assertTrue(result["complete"])  # raw coverage only, not eligibility for canonical publication.
        c = sqlite3.connect(self.root / "stage/staging.sqlite3")
        try:
            reasons = [r[0] for r in c.execute("SELECT reason FROM staging_items ORDER BY row_position")]
            self.assertEqual(reasons, ["invalid_file_date", "invalid_file_number", "required_file_field_missing"])
        finally:
            c.close()

    def test_registry_mapping_and_row_counts_are_explicit_and_raw_mutation_blocks_reuse(self):
        path = self.csv()
        self.source["expected_rows"] = 3
        result = self.stage(path)
        self.assertFalse(result["complete"])
        self.source.pop("mapping_version")
        with self.assertRaisesRegex(CollectionError, "mapping_version"):
            self.stage(path, "unversioned")
        self.source["mapping_version"] = "fixture_mapping_v1"
        self.register()
        raw = self.root / "stage/raw/source.csv"
        raw.write_bytes(b"changed")
        with self.assertRaisesRegex(CollectionError, "file_stage_integrity_failed"):
            stage_file(registry_path=self.registry, source_id=self.source["source_id"], input_path=path, output=self.root / "stage")

    def test_structural_parse_failure_preserves_raw_and_is_not_success_zero(self):
        path = self.root / "bad.csv"
        path.write_text("date,date,label\n2026-09-15,1234,실패자료\n", encoding="utf-8")
        with self.assertRaisesRegex(CollectionError, "invalid_or_duplicate_headers"):
            self.stage(path)
        manifest = read_json(self.root / "stage/manifest.json")
        self.assertEqual(manifest["state"], "parsing_failed")
        self.assertFalse(manifest["complete"])
        self.assertEqual(manifest["staging_rows_committed"], 0)
        self.assertEqual(digest_file(self.root / "stage/raw/source.csv"), digest_file(path))
        with self.assertRaisesRegex(CollectionError, "parsing_failed_use_new_directory"):
            stage_file(registry_path=self.registry, source_id=self.source["source_id"], input_path=path, output=self.root / "stage")

    def test_json_decimal_currency_does_not_round_before_integer_krw_mapping(self):
        self.source["format"] = "json"
        self.source["expected_rows"] = 1
        self.source["field_mapping"]["amount"]["unit"] = "krw"
        path = self.root / "large-number.json"
        path.write_text('[{"date":"2026-09-15","amount":9007199254740993.0,"label":"정확한 원"}]', encoding="utf-8")
        self.stage(path)
        c = sqlite3.connect(self.root / "stage/staging.sqlite3")
        try:
            standard = json.loads(c.execute("SELECT standard_json FROM staging_items").fetchone()[0])
            self.assertEqual(standard["amount"], 9007199254740993)
        finally:
            c.close()

    def test_distinct_json_array_selections_have_distinct_raw_row_identity(self):
        self.source["format"] = "json"
        self.source["expected_rows"] = 1
        path = self.root / "selections.json"
        path.write_text(json.dumps({"A": [self.rows()[0]], "B": [self.rows()[0]]}), encoding="utf-8")
        self.source["items_path"] = ["A"]
        first = self.stage(path, "selection-a")
        self.source["items_path"] = ["B"]
        second = self.stage(path, "selection-b")
        identifiers = []
        for name in ("selection-a", "selection-b"):
            c = sqlite3.connect(self.root / name / "staging.sqlite3")
            try:
                identifiers.append(c.execute("SELECT observation_id FROM staging_items").fetchone()[0])
            finally:
                c.close()
        self.assertNotEqual(identifiers[0], identifiers[1])
        self.assertEqual(first["sections"], {"json:/A": 1})
        self.assertEqual(second["sections"], {"json:/B": 1})


if __name__ == "__main__":
    unittest.main()

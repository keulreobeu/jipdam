"""Fictional file sources exercise preservation through canonical publication."""
import csv
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from budongi.collection import CollectionError, digest_file, read_json, write_json
from budongi.collection_integrate import integrate_file, SCHEMA_VERSION
from budongi.source_files import stage_file


class FileCanonicalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = self.root / "registry.json"
        self.source = {"source_id": "fictional_rent", "dataset_id": "fictional_rent_dataset",
            "documentation": "https://example.invalid/fictional", "format": "csv", "record_type": "rental",
            "status": "approved", "approval_ref": "unit fixture only", "scope": "fictional Seoul rows",
            "fictional": True, "mapping_version": "fixture_v1", "expected_rows": 4,
            "field_mapping": {field: {"column": field, "type": kind, "required": True,
                                      **({"unit": "krw"} if kind == "amount_krw" else {})}
                for field, kind in {"sgg_cd": "string", "contract_date": "date", "apartment_name": "string",
                    "area_sqm": "number", "deposit_krw": "amount_krw", "monthly_rent_krw": "amount_krw"}.items()}}
        row = {"sgg_cd": "11110", "contract_date": "2026-09-15", "apartment_name": "가상 단지",
               "area_sqm": "84.5", "deposit_krw": "9007199254740993", "monthly_rent_krw": "0"}
        self.rows = [row.copy(), row.copy(), row | {"sgg_cd": "11140", "contract_date": "2026-10-01"},
                     row | {"contract_date": "2024-01-01"}]

    def register(self):
        write_json(self.registry, {"schema_version": "source_registry_v1", "sources": [self.source]})

    def input(self):
        path = self.root / ("input." + self.source["format"])
        if self.source["format"] == "csv":
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(self.rows[0]))
                writer.writeheader()
                writer.writerows(self.rows)
        elif self.source["format"] == "json":
            path.write_text(json.dumps({"data": self.rows}), encoding="utf-8")
            self.source["items_path"] = ["data"]
        else:
            from openpyxl import Workbook
            book = Workbook()
            book.remove(book.active)
            for name, rows in (("서울 A", self.rows[:2]), ("서울 B", self.rows[2:]), ("빈 시트", [])):
                sheet = book.create_sheet(name)
                if rows:
                    sheet.append(list(rows[0]))
                    for row in rows:
                        sheet.append(list(row.values()))
            book.save(path)
            book.close()
            self.source["sheets"] = ["서울 A", "서울 B", "빈 시트"]
            self.source["expected_rows_by_section"] = {"서울 A": 2, "서울 B": 2, "빈 시트": 0}
        return path

    def stage(self, name="stage"):
        path = self.input()
        self.register()
        stage_file(registry_path=self.registry, source_id=self.source["source_id"], input_path=path, output=self.root / name)
        return self.root / name

    def integrate(self, stage, name="canonical", batch="fixture", previous=None):
        return integrate_file(stage, self.registry, self.root / name, batch_id=batch,
            snapshot_date="2026-10-12", observation_from="2025-10-12", record_url="https://example.invalid/fixture",
            previous=previous)

    @unittest.skipUnless(os.name == "nt", "Windows lock contention")
    def test_stage_and_canonical_publish_after_transient_windows_denial(self):
        actual_rename = os.rename
        attempted = set()

        def rename(source, output):
            name = Path(source).name
            kind = next((prefix for prefix in (".file-stage-", ".canonical-build-") if name.startswith(prefix)), None)
            if kind and kind not in attempted:
                attempted.add(kind)
                error = PermissionError(13, "synthetic access denial")
                error.winerror = 5
                raise error
            actual_rename(source, output)

        with patch("budongi.collection.os.rename", side_effect=rename), patch("budongi.collection.time.sleep"):
            report = self.integrate(self.stage())
        self.assertEqual(attempted, {".file-stage-", ".canonical-build-"})
        self.assertEqual(report["counts"]["observations"], 3)
        self.assertTrue((self.root / "canonical" / "canonical.sqlite3").is_file())

    def test_all_formats_keep_equal_rows_scope_exclusions_exact_won_and_lineage(self):
        with patch("budongi.collection._open_request", side_effect=AssertionError("network forbidden")), \
                patch("budongi.credential_vault.CredentialVault", side_effect=AssertionError("vault forbidden")):
            for format_name in ("csv", "json", "xlsx"):
                with self.subTest(format=format_name):
                    self.source["format"] = format_name
                    stage = self.stage("stage-" + format_name)
                    report = self.integrate(stage, "canonical-" + format_name)
                    self.assertEqual(report["schema_version"], SCHEMA_VERSION)
                    self.assertEqual(report["counts"]["raw_items"], 4)
                    self.assertEqual(report["counts"]["observations"], 3)
                    self.assertEqual(report["lineage_join"], 3)
                    self.assertEqual(report["stage_counts"], {"valid": 3, "outside_period": 1})
                    self.assertEqual(report["quality_status"], "synthetic")
                    c = sqlite3.connect(self.root / ("canonical-" + format_name) / "canonical.sqlite3")
                    try:
                        self.assertEqual(c.execute("SELECT COUNT(DISTINCT observation_id) FROM observations").fetchone()[0], 3)
                        self.assertEqual(c.execute("SELECT DISTINCT deposit_krw FROM observations").fetchall(), [(9007199254740993,)])
                        self.assertEqual(c.execute("SELECT sgg_cd,contract_month FROM batch_files").fetchone(), (None, None))
                        self.assertEqual(c.execute("SELECT COUNT(*) FROM coverage").fetchone()[0], 3)
                        with self.assertRaises(sqlite3.IntegrityError):
                            c.execute("DELETE FROM observations")
                    finally:
                        c.close()
                    if format_name == "xlsx":
                        self.assertEqual(report["empty_sections"], ["빈 시트"])

    def test_repeat_new_batch_and_mapping_version_reuse_raw_and_preserve_previous(self):
        stage = self.stage()
        first = self.integrate(stage)
        previous = self.root / "canonical"
        before = digest_file(previous / "canonical.sqlite3")
        replay = self.integrate(stage, "replay", previous=previous)
        self.assertTrue(replay["reused_batch"])
        self.assertFalse(any(replay["new_counts"].values()))
        overlap = self.integrate(stage, "overlap", batch="second", previous=previous)
        self.assertEqual(overlap["new_counts"]["observations"], 0)
        self.assertEqual(overlap["new_counts"]["batch_observations"], 3)
        self.source["mapping_version"] = "fixture_v2"
        staged_v2 = self.stage("stage-v2")
        changed = self.integrate(staged_v2, "version-v2", previous=previous)
        self.assertEqual(changed["new_counts"]["raw_items"], 0)
        self.assertEqual(changed["new_counts"]["observations"], 3)
        self.assertEqual(first["counts"]["observations"], 3)
        self.assertEqual(before, digest_file(previous / "canonical.sqlite3"))

    def test_rejected_count_contract_and_raw_changes_block_publication(self):
        for condition in ("negative", "count", "unit", "contract", "raw", "mapped"):
            with self.subTest(condition=condition):
                self.source["expected_rows"] = 5 if condition == "count" else 4
                self.source["field_mapping"]["deposit_krw"]["unit"] = "unknown" if condition == "unit" else "krw"
                self.rows[0]["area_sqm"] = "-1" if condition == "negative" else "84.5"
                stage = self.stage("stage-" + condition)
                if condition == "contract":
                    self.source["approval_ref"] = "different approved contract"
                    self.register()
                if condition == "raw":
                    raw_ref = read_json(stage / "manifest.json")["raw_file"]
                    (stage / raw_ref).write_bytes(b"changed")
                if condition == "mapped":
                    # Recomputed DB checksum alone must not endorse values that
                    # disagree with the preserved original and mapping contract.
                    c = sqlite3.connect(stage / "staging.sqlite3")
                    try:
                        c.execute("DROP TRIGGER seal_staging_items_UPDATE")
                        identifier, payload = c.execute("SELECT observation_id,standard_json FROM staging_items LIMIT 1").fetchone()
                        changed = json.loads(payload)
                        changed["deposit_krw"] += 1
                        c.execute("UPDATE staging_items SET standard_json=? WHERE observation_id=?", (json.dumps(changed), identifier))
                        c.commit()
                    finally:
                        c.close()
                    manifest = read_json(stage / "manifest.json")
                    manifest["staging_sha256"] = digest_file(stage / "staging.sqlite3")
                    write_json(stage / "manifest.json", manifest)
                with self.assertRaises(CollectionError):
                    self.integrate(stage, "blocked-" + condition)
                self.assertFalse((self.root / ("blocked-" + condition)).exists())

    def test_same_batch_changed_input_rolls_back_and_quality_domains_do_not_mix(self):
        stage = self.stage()
        self.integrate(stage)
        previous = self.root / "canonical"
        before = digest_file(previous / "canonical.sqlite3")
        self.rows[0]["apartment_name"] = "다른 가상 단지"
        changed = self.stage("changed")
        with self.assertRaisesRegex(CollectionError, "same_batch_different_input"):
            self.integrate(changed, "failed", previous=previous)
        self.assertEqual(before, digest_file(previous / "canonical.sqlite3"))
        self.assertFalse((self.root / "failed").exists())
        self.assertEqual(list(self.root.glob(".canonical-build-*")), [])
        self.source["fictional"] = False
        actual_labeled = self.stage("actual-labeled-fixture")
        with self.assertRaisesRegex(CollectionError, "quality_domains_must_not_mix"):
            self.integrate(actual_labeled, "no-mix", batch="second", previous=previous)

    def test_sale_and_official_complex_building_ids_are_distinct_from_source_transaction(self):
        self.source["record_type"] = "sale"
        self.source["field_mapping"].pop("deposit_krw")
        self.source["field_mapping"].pop("monthly_rent_krw")
        self.source["field_mapping"]["price_krw"] = {"column": "price_krw", "type": "amount_krw", "unit": "krw", "required": True}
        for field in ("source_complex_id", "source_building_id", "source_record_id", "legal_dong_code", "main_number", "sub_number", "land_code"):
            self.source["field_mapping"][field] = {"column": field, "type": "string"}
        self.source["official_identifiers"] = {
            "complex": {"namespace": "fictional:complex", "basis": "fictional official fixture identifier"},
            "building": {"namespace": "fictional:building", "basis": "fictional official fixture identifier"}}
        self.source["address_basis"] = "fictional official cadastral fixture components"
        for row in self.rows:
            row.pop("deposit_krw")
            row.pop("monthly_rent_krw")
            row.update(price_krw="12340000", source_complex_id="C1", source_building_id="B1", source_record_id="T1",
                       legal_dong_code="16000", main_number="1", sub_number="0", land_code="1")
        report = self.integrate(self.stage())
        self.assertEqual(report["counts"]["complexes"], 1)
        self.assertEqual(report["counts"]["buildings"], 1)
        self.assertEqual(report["counts"]["addresses"], 1)
        self.assertEqual(report["counts"]["complex_address_evidence"], 2)
        self.assertEqual(report["counts"]["identity_conflicts"], 2)  # The different-region row keeps its fact.
        self.assertEqual(report["counts"]["observations"], 3)
        c = sqlite3.connect(self.root / "canonical/canonical.sqlite3")
        try:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM observations WHERE complex_id IS NOT NULL AND building_id IS NOT NULL AND source_record_id='T1'").fetchone()[0], 2)
        finally:
            c.close()

    def test_cli_staging_and_canonical_publication(self):
        path = self.input()
        self.register()
        prefix = [sys.executable, "-X", "utf8", "-m", "budongi.cli", "collection"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
        stage = self.root / "cli-stage"
        commands = [prefix + ["stage-file", "--registry", str(self.registry), "--source-id", self.source["source_id"],
                    "--input", str(path), "--output", str(stage)],
            prefix + ["integrate-file", "--registry", str(self.registry), "--directory", str(stage),
                    "--output", str(self.root / "cli-db"), "--batch-id", "cli-fixture", "--snapshot-date", "2026-10-12",
                    "--observation-from", "2025-10-12", "--record-url", "https://example.invalid/fixture"]]
        for command in commands:
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertTrue(report["complete"])
        self.assertEqual(report["lineage_join"], 3)

    def test_replay_after_new_entity_batch_does_not_rewrite_old_candidate_snapshot(self):
        self.source["official_identifiers"] = {"complex": {"namespace": "fictional:complex", "basis": "fixture official ID"}}
        for field in ("source_complex_id", "legal_dong", "jibun"):
            self.source["field_mapping"][field] = {"column": field, "type": "string"}
        for row in self.rows:
            row.update(source_complex_id=None, legal_dong="가상동", jibun="1-1")
        first_stage = self.stage("before-stage")
        self.integrate(first_stage, "before")
        for row in self.rows:
            row["source_complex_id"] = "C1"
        second_stage = self.stage("after-stage")
        self.integrate(second_stage, "after", batch="new-entity", previous=self.root / "before")
        replay = self.integrate(first_stage, "after-replay", previous=self.root / "after")
        self.assertTrue(replay["reused_batch"])
        self.assertFalse(any(replay["new_counts"].values()))

    def test_unregistered_and_unapproved_inputs_never_publish(self):
        stage = self.stage()
        self.source["status"] = "draft"
        self.register()
        with self.assertRaisesRegex(CollectionError, "approved_registry_scope"):
            self.integrate(stage, "unapproved")
        write_json(self.registry, {"schema_version": "source_registry_v1", "sources": []})
        with self.assertRaisesRegex(CollectionError, "approved_registry_scope"):
            self.integrate(stage, "unregistered")
        self.assertFalse((self.root / "unapproved").exists())
        self.assertFalse((self.root / "unregistered").exists())

    def test_different_json_selections_reuse_blob_but_keep_distinct_file_views_and_rows(self):
        self.source["format"] = "json"
        path = self.root / "selections.json"
        path.write_text(json.dumps({"A": self.rows[:2], "B": self.rows[2:3]}), encoding="utf-8")
        reports = []
        for selector, expected in (("A", 2), ("B", 1)):
            self.source["items_path"] = [selector]
            self.source["expected_rows"] = expected
            self.register()
            stage = self.root / ("stage-" + selector)
            stage_file(registry_path=self.registry, source_id=self.source["source_id"], input_path=path, output=stage)
            reports.append(self.integrate(stage, "canonical-" + selector, batch=selector,
                previous=self.root / "canonical-A" if selector == "B" else None))
        self.assertEqual(reports[1]["counts"]["raw_blobs"], 1)
        self.assertEqual(reports[1]["counts"]["raw_files"], 2)
        self.assertEqual(reports[1]["counts"]["raw_items"], 3)
        self.assertEqual(reports[1]["counts"]["observations"], 3)


if __name__ == "__main__":
    unittest.main()

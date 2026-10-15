"""Canonical boundary regressions; synthesized input is never real coverage."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from budongi.collection import CollectionError, create_plan, digest_file, fetch_collection, load_query, query_folder, read_json, write_json
from budongi.collection_db import build_databases, pack_collection, validate_normalized_inputs
from budongi.collection_integrate import SCHEMA, SCHEMA_VERSION, KEYS, integrate_collection
from test_collection import RECORD, Response, Vault, item, payload


class IntegrationInputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "batch"

    def archive(self, *, partial=False):
        create_plan(self.root, batch_id="integration-test", snapshot_date="2026-10-12",
                    districts=["11110"], months=["202609", "202610"] if partial else ["202609"],
                    services=["rental"], record_url=RECORD)
        fetch_collection(self.root, {"rental": "fixture-id"}, vault=Vault(),
                         opener=lambda *a, **k: Response(payload([item()])), sleep=lambda _: None,
                         limit=1 if partial else None)
        build_databases(self.root, self.root / "db", allow_partial=partial)

    def test_current_normalized_input_binding_rejects_changed_raw_with_same_count(self):
        self.archive()
        validate_normalized_inputs(self.root, self.root / "db")
        plan = read_json(self.root / "plan.json")
        folder = query_folder(self.root, "rental", "11110", "202609")
        manifest = load_query(self.root, plan, "rental", "11110", "202609")
        page = manifest["pages"][0]
        modified = payload([item(name="다른 실제 입력을 흉내낸 합성 단지")])
        (folder / page["file"]).write_bytes(modified)
        page["sha256"] = hashlib.sha256(modified).hexdigest()
        for attempt in manifest["attempts"]:
            if attempt.get("file") == page["file"]:
                attempt["sha256"] = page["sha256"]
        write_json(folder / "manifest.json", manifest)
        with patch("budongi.collection._open_request", side_effect=AssertionError("Network forbidden")), \
                patch("budongi.credential_vault.CredentialVault", side_effect=AssertionError("Vault forbidden")):
            for action in (lambda: integrate_collection(self.root, self.root / "db", self.root / "canonical"),
                           lambda: pack_collection(self.root, self.root / "bad.zip", db_directory=self.root / "db")):
                with self.assertRaisesRegex(CollectionError, "stale_database"):
                    action()
        self.assertFalse((self.root / "canonical").exists())
        self.assertFalse((self.root / "bad.zip").exists())

    def test_partial_inputs_require_explicit_policy_and_changed_plan_is_rejected(self):
        self.archive(partial=True)
        with self.assertRaisesRegex(CollectionError, "incomplete_collection"):
            integrate_collection(self.root, self.root / "db", self.root / "canonical")
        validate_normalized_inputs(self.root, self.root / "db", allow_partial=True)
        plan = read_json(self.root / "plan.json")
        plan["record_url"] = "https://github.com/keulreobeu/jipdam/issues/6"
        write_json(self.root / "plan.json", plan)
        with self.assertRaisesRegex(CollectionError, "stale_database"):
            validate_normalized_inputs(self.root, self.root / "db", allow_partial=True)

    def test_database_manifest_requires_exact_declared_outputs_and_hashes(self):
        self.archive()
        manifest_path = self.root / "db/normalized-manifest.json"
        manifest = read_json(manifest_path)
        original = dict(manifest["files"])
        write_json(manifest_path, [])
        with self.assertRaisesRegex(CollectionError, "invalid_manifest"):
            validate_normalized_inputs(self.root, self.root / "db")
        manifest["files"].pop("staging.sqlite3")
        write_json(manifest_path, manifest)
        with self.assertRaisesRegex(CollectionError, "database_manifest_mismatch"):
            validate_normalized_inputs(self.root, self.root / "db")
        manifest["files"] = original
        write_json(manifest_path, manifest)
        with (self.root / "db/rental.sqlite3").open("ab") as output:
            output.write(b"corrupted-derived-content")
        with self.assertRaisesRegex(CollectionError, "database_integrity_failed"):
            validate_normalized_inputs(self.root, self.root / "db")


class CanonicalSnapshotTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)

    def archive(self, name="batch", *, conflict=False, masked_labels=False):
        root = self.base / name
        create_plan(root, batch_id=name, snapshot_date="2026-10-12", districts=["11110"],
                    months=["202609"], services=["rental", "trade", "trade-detail"], record_url=RECORD)
        def response(request, **kwargs):
            if "AptRent" in request.full_url:
                rows = [item(), item()]
                if masked_labels:
                    for row in rows:
                        row.update(aptNm="***", umdNm="***", jibun="***")
            elif "AptTradeDev" in request.full_url:
                rows = [item(service="trade"), item(service="trade")]
                rows[0].update(umdCd="18000", bonbun="126", bubun="0", landCd="1")
                rows[1].update(aptSeq="11140-101" if conflict else "11110-101",
                               umdCd="18000", bonbun="0126", bubun="0000", landCd="1")
            else:
                rows = [item(service="trade")]
                if masked_labels:
                    rows[0].update(aptNm="***", umdNm="***", jibun="***")
            return Response(payload(rows))
        fetch_collection(root, {s: "fixture" for s in ("rental", "trade", "trade-detail")},
                         vault=Vault(), opener=response, sleep=lambda _: None)
        build_databases(root, root / "db")
        return root

    def test_identical_replay_and_overlapping_batch_keep_facts_and_separate_membership(self):
        root = self.archive()
        first = self.base / "canonical"
        with patch("budongi.collection._open_request", side_effect=AssertionError("Network forbidden")), \
                patch("budongi.credential_vault.CredentialVault", side_effect=AssertionError("Vault forbidden")):
            report = integrate_collection(root, root / "db", first)
            original_hash = digest_file(first / "canonical.sqlite3")
            replay = integrate_collection(root, root / "db", self.base / "replay", previous=first)
            self.assertTrue(replay["reused_batch"])
            self.assertTrue(all(v == 0 for v in replay["new_counts"].values()))
            second = self.base / "new-batch"
            shutil.copytree(root, second)
            plan = read_json(second / "plan.json")
            plan["batch_id"] = "new-batch"
            write_json(second / "plan.json", plan)
            build_databases(second, second / "db-new")
            added = integrate_collection(second, second / "db-new", self.base / "incremental", previous=first)
        self.assertEqual(report["batch_counts"], {"raw_rows": 5, "valid": 5})
        self.assertEqual(added["new_counts"]["observations"], 0)
        self.assertEqual(added["new_counts"]["raw_items"], 0)
        self.assertEqual(added["new_counts"]["batch_observations"], 5)
        self.assertEqual(added["counts"]["batches"], 2)
        self.assertEqual(added["counts"]["batch_observations"], 10)
        self.assertEqual(original_hash, digest_file(first / "canonical.sqlite3"))
        c = sqlite3.connect(first / "canonical.sqlite3")
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("DELETE FROM observations")
        finally:
            c.close()

    def test_official_entities_share_address_evidence_but_labels_only_create_pending_candidates(self):
        root = self.archive()
        report = integrate_collection(root, root / "db", self.base / "canonical")
        self.assertEqual(report["counts"]["complexes"], 2)
        self.assertEqual(report["counts"]["addresses"], 1)
        self.assertEqual(report["counts"]["buildings"], 0)
        self.assertEqual(report["counts"]["match_candidates"], 6)
        self.assertEqual(report["official_complex_join"], 2)
        self.assertEqual(report["lineage_join"], 5)
        c = sqlite3.connect(self.base / "canonical/canonical.sqlite3")
        try:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM observations WHERE kind!='sale' AND complex_id IS NOT NULL").fetchone()[0], 0)
            self.assertEqual(c.execute("SELECT DISTINCT review_status,confidence,confidence_score FROM match_candidates").fetchall(), [("pending", "unverified", None)])
            self.assertEqual(c.execute("SELECT COUNT(*) FROM observations WHERE source_effective_from IS NOT NULL OR building_id IS NOT NULL").fetchone()[0], 0)
        finally:
            c.close()

    def test_masked_labels_do_not_create_literal_identity_candidates(self):
        root = self.archive(masked_labels=True)
        report = integrate_collection(root, root / "db", self.base / "canonical")
        self.assertEqual(report["counts"]["complexes"], 2)
        self.assertEqual(report["counts"]["match_candidates"], 0)
        c = sqlite3.connect(self.base / "canonical/canonical.sqlite3")
        try:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM match_candidates").fetchone()[0], 0)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM observations WHERE kind!='sale' AND complex_id IS NOT NULL").fetchone()[0], 0)
        finally:
            c.close()

    def test_region_conflict_is_recorded_and_not_promoted_to_an_official_link(self):
        root = self.archive(conflict=True)
        report = integrate_collection(root, root / "db", self.base / "canonical")
        self.assertEqual(report["counts"]["identity_conflicts"], 1)
        self.assertEqual(report["counts"]["complexes"], 1)
        self.assertEqual(report["counts"]["observations"], 5)
        self.assertEqual(report["official_complex_join"], 1)

    def test_changed_same_batch_rolls_back_and_previous_snapshot_hash_is_preserved(self):
        root = self.archive()
        previous = self.base / "canonical"
        integrate_collection(root, root / "db", previous)
        before = digest_file(previous / "canonical.sqlite3")
        plan = read_json(root / "plan.json")
        plan["record_url"] = "https://github.com/keulreobeu/jipdam/issues/6"
        write_json(root / "plan.json", plan)
        build_databases(root, root / "db-new")
        with self.assertRaisesRegex(CollectionError, "same_batch_different_input"):
            integrate_collection(root, root / "db-new", self.base / "bad-output", previous=previous)
        self.assertFalse((self.base / "bad-output").exists())
        self.assertEqual(before, digest_file(previous / "canonical.sqlite3"))
        self.assertEqual(list(self.base.glob(".canonical-build-*")), [])

    def test_new_normalization_version_keeps_previous_facts_and_reuses_raw_rows(self):
        root = self.archive()
        previous = self.base / "canonical"
        integrate_collection(root, root / "db", previous)
        # Synthetic parser-version transition; not a claim of new actual source data.
        with patch("budongi.collection_db.NORMALIZATION_VERSION", "molit_normalization_fixture_v2"):
            build_databases(root, root / "db-version2")
            report = integrate_collection(root, root / "db-version2", self.base / "version2", previous=previous)
        self.assertEqual(report["counts"]["batches"], 2)
        self.assertEqual(report["counts"]["observations"], 10)
        self.assertEqual(report["new_counts"]["raw_items"], 0)
        self.assertEqual(report["lineage_join"], 5)

    def test_cli_previous_snapshot_and_modified_previous_db(self):
        root = self.archive()
        previous = self.base / "canonical"
        integrate_collection(root, root / "db", previous)
        command = [sys.executable, "-m", "budongi.cli", "collection", "integrate", "--directory", str(root),
                   "--previous", str(previous), "--output", str(self.base / "cli-replay")]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["reused_batch"])
        with (previous / "canonical.sqlite3").open("ab") as output:
            output.write(b"changed-previous")
        with self.assertRaisesRegex(CollectionError, "previous_canonical_integrity_failed"):
            integrate_collection(root, root / "db", self.base / "bad-previous", previous=previous)
        self.assertFalse((self.base / "bad-previous").exists())

    def test_row_lineage_lookup_does_not_scan_entire_batch_for_each_observation(self):
        root = self.base / "scale-fixture"
        create_plan(root, batch_id="scale-fixture", snapshot_date="2026-10-12", districts=["11110"],
                    months=["202609"], services=["rental"], record_url=RECORD)
        fetch_collection(root, {"rental": "fixture"}, vault=Vault(),
                         opener=lambda *a, **k: Response(payload([item()] * 1000)), sleep=lambda _: None)
        build_databases(root, root / "db")
        original_connect = sqlite3.connect
        steps = [0]
        def connect(*args, **kwargs):
            c = original_connect(*args, **kwargs)
            if str(args[0]).endswith("canonical.sqlite3"):
                def bound_sql_work():
                    steps[0] += 1000
                    return int(steps[0] > 5_000_000)
                c.set_progress_handler(bound_sql_work, 1000)
            return c
        # This measures real SQLite work, not a timing guess or an implementation-string assertion.
        with patch("budongi.collection_integrate.sqlite3.connect", side_effect=connect):
            report = integrate_collection(root, root / "db", self.base / "scale-canonical")
        self.assertEqual(report["lineage_join"], 1000)
        self.assertLess(steps[0], 5_000_000)

    def test_canonical_pk_fk_not_null_and_check_are_enforced_before_sealing(self):
        c = sqlite3.connect(":memory:")
        self.addCleanup(c.close)
        c.executescript(SCHEMA)
        c.execute("INSERT INTO sources VALUES ('source','dataset','xml','documentation')")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "UNIQUE"):
            c.execute("INSERT INTO sources VALUES ('source','other','xml','documentation')")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL"):
            c.execute("INSERT INTO sources VALUES ('other',NULL,'xml','documentation')")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "CHECK"):
            c.execute("INSERT INTO regions VALUES ('11','잘못된 코드')")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            c.execute("INSERT INTO raw_files VALUES ('file','source','missing.xml',?,1)", ("0" * 64,))

    def test_previous_v2_migrates_only_new_copy_and_preserves_every_table_value(self):
        root = self.archive()
        previous = self.base / "v2"
        v2_schema = SCHEMA.replace("PRAGMA user_version=3", "PRAGMA user_version=2").replace(
            "sgg_cd TEXT REFERENCES regions, contract_month TEXT, retrieved_at_utc",
            "sgg_cd TEXT NOT NULL REFERENCES regions, contract_month TEXT NOT NULL, retrieved_at_utc")
        with patch("budongi.collection_integrate.SCHEMA", v2_schema), \
                patch("budongi.collection_integrate.SCHEMA_VERSION", "canonical_real_estate_v2"):
            integrate_collection(root, root / "db", previous)
        before = digest_file(previous / "canonical.sqlite3")
        upgraded = self.base / "v3"
        report = integrate_collection(root, root / "db", upgraded, previous=previous)
        self.assertEqual(report["schema_version"], SCHEMA_VERSION)
        self.assertFalse(any(report["new_counts"].values()))
        with closing(sqlite3.connect(previous / "canonical.sqlite3")) as old, closing(sqlite3.connect(upgraded / "canonical.sqlite3")) as new:
            self.assertEqual(old.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual(new.execute("PRAGMA user_version").fetchone()[0], 3)
            for table, keys in KEYS.items():
                query = "SELECT * FROM " + table + " ORDER BY " + ",".join(keys)
                self.assertEqual(old.execute(query).fetchall(), new.execute(query).fetchall(), table)
        self.assertEqual(digest_file(previous / "canonical.sqlite3"), before)


if __name__ == "__main__":
    unittest.main()

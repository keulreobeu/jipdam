"""Role separation rules of tooling/role2_harness/role_guard.py (no models are called)."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("role_guard", ROOT / "tooling" / "role2_harness" / "role_guard.py")
role_guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(role_guard)


class RoleGuardTests(unittest.TestCase):
    def test_family_comes_from_model_slug_not_tool(self):
        self.assertEqual(role_guard.identify("claude-sonnet-5-5-high"), ("anthropic", "sonnet"))
        self.assertEqual(role_guard.identify("gemini-3.8-flash"), ("google", "gemini"))
        self.assertEqual(role_guard.identify("gpt-oss-120b-medium"), ("openai", "gpt-oss"))
        with self.assertRaisesRegex(role_guard.RoleError, "model_banned:gms"):
            role_guard.identify("gpt-6.1-sol")

    def test_contractor_auditor_referee_must_be_distinct_families(self):
        ok = role_guard.check_roles(contractor="agy:gemini-3.8-flash", auditor="sonnet", referee="haiku")
        self.assertEqual(ok["contractor"]["family"], "gemini")
        role_guard.check_roles(contractor="claude:sonnet", auditor="haiku", referee="fable")
        for kwargs, code in [
            ({"contractor": "agy:claude-opus-5-5-high"}, "R1_contractor_is_lead_family"),
            ({"contractor": "claude:opus"}, "R1_contractor_is_lead_family"),
            ({"contractor": "agy:claude-sonnet-5-5", "auditor": "sonnet"}, "R2_auditor_family_conflict"),
            ({"contractor": "agy:gemini-3.8-flash", "auditor": "gemini-4-argon"}, "R2_auditor_family_conflict"),
            ({"contractor": "agy:gemini-3.8-flash", "auditor": "sonnet", "referee": "sonnet"},
             "R3_referee_family_conflict"),
            ({"contractor": "claude:sonnet", "auditor": "haiku", "referee": "opus"}, "R3_referee_family_conflict"),
        ]:
            with self.subTest(code=code), self.assertRaisesRegex(role_guard.RoleError, code):
                role_guard.check_roles(**kwargs)

    def test_agy_inputs_exclude_hidden_tests_data_and_repo_workdirs(self):
        role_guard.check_inputs(["C:/tmp/spec/tests/test_x.py"], workdir="C:/Users/x/AppData/Local/agy-r2/u1")
        with self.assertRaisesRegex(role_guard.RoleError, "R5_forbidden_input"):
            role_guard.check_inputs(["C:/tmp/spec/hidden/test_x_hidden.py"], workdir=None)
        with self.assertRaisesRegex(role_guard.RoleError, "R5_workdir_inside_repo"):
            role_guard.check_inputs([], workdir=str(ROOT / "outputs"))

    def test_verify_run_reads_actual_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            good = run / "units" / "C1"
            good.mkdir(parents=True)
            (good / "attempt_1.json").write_text(json.dumps({"agy": {"model": "gemini-3.8-flash-medium"}}), encoding="utf-8")
            sneaky = run / "units" / "C2"
            (sneaky / "attempt_1.agy_task" / "s1").mkdir(parents=True)
            (sneaky / "attempt_1.json").write_text(json.dumps({"agy": {}}), encoding="utf-8")
            (sneaky / "attempt_1.agy_task" / "s1" / "events.jsonl").write_text(
                json.dumps({"type": "init", "model": "claude-opus-5-5-high"}) + "\n", encoding="utf-8")
            unknown = run / "units" / "C3"
            unknown.mkdir(parents=True)
            (unknown / "attempt_1.json").write_text(json.dumps({"agy": {}}), encoding="utf-8")
            report = role_guard.verify_run(run, contractor="agy:gemini-3.8-flash")
            self.assertTrue(report["units"]["C1"]["ok"])
            self.assertFalse(report["units"]["C2"]["ok"])
            self.assertEqual(report["units"]["C3"], "model_unverified")
            self.assertEqual((report["violations"], report["unverified"]), (1, 1))


ORACLE_SPEC = importlib.util.spec_from_file_location("importer_oracle",
                                                     ROOT / "tooling" / "role2_harness" / "importer_oracle.py")
importer_oracle = importlib.util.module_from_spec(ORACLE_SPEC)
ORACLE_SPEC.loader.exec_module(importer_oracle)


class FakeImporter:
    """Stands in for the pinned team importer: records what the oracle registered."""
    PACKAGES = {}

    def build(self, root, database):
        (alias, spec), = self.PACKAGES.items()
        self.seen = (alias, spec, sorted(p.name for p in (root / Path(alias).stem).rglob("manifest.json")))
        return {"database": str(database), "counts": {spec[0]: {"accepted": spec[4], "rejected": 0}}}


class ImporterOracleTests(unittest.TestCase):
    def test_oracle_registers_only_the_given_zip_after_extracting_it(self):
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "pkg.zip"
            manifest = {"source_id": "s", "batch_id": "s-20261029-v1", "record_type": "facility",
                        "counts": {"accepted": 2}, "files": [{"path": "normalized/facility.jsonl", "format": "jsonl",
                                                               "rows": 2}]}
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("s/s-20261029-v1/manifest.json", json.dumps(manifest))
                zf.writestr("s/s-20261029-v1/normalized/facility.jsonl", "{}\n{}\n")
            fake = FakeImporter()
            report = importer_oracle.run_oracle(archive, work=Path(tmp) / "work", issue=42, importer=fake)
            self.assertTrue(report["ok"])
            alias, spec, manifests = fake.seen
            self.assertEqual((alias, spec[:5], spec[6], manifests),
                             ("t.zip", ("s", "s-20261029-v1", "facility", 2, 2), 42, ["manifest.json"]))
            with self.assertRaisesRegex(ValueError, "work_not_empty"):
                importer_oracle.run_oracle(archive, work=Path(tmp) / "work", issue=42, importer=fake)


if __name__ == "__main__":
    unittest.main()

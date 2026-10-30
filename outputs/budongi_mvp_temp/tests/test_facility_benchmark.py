"""Non-billing checks for sealed inputs, one-variable prompts and independent gates."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/benchmark_facility.py"
spec = importlib.util.spec_from_file_location("facility_benchmark_driver", SCRIPT)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class FacilityBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / ".local_runtime/bench"
        for name in (driver.SPEC, driver.EVAL, driver.APP + "docs/specs/30_context_benchmark_spec.md",
                     driver.APP + "scripts/benchmark_facility.py", driver.APP + "src/jipdam_harness/execution.py",
                     driver.APP + "src/jipdam_harness/managed.py", "AGENTS.md", driver.APP + "AGENTS.md"):
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Fixed synthetic benchmark input: " + name, encoding="utf-8")
        self.preflight = patch.object(driver, "preflight", return_value={"cli_version": "0.164.0", "authentication": "chatgpt"})
        self.preflight.start(); self.addCleanup(self.preflight.stop)
        self.git = patch.object(driver, "git", side_effect=lambda root, *args: "a" * 40 if args == ("rev-parse", "HEAD") else "")
        self.git.start(); self.addCleanup(self.git.stop)

    def test_seal_is_repeatable_and_does_not_call_a_model(self):
        with patch.object(driver.Orchestrator, "run", side_effect=AssertionError("model must not run during seal")):
            first = driver.seal(self.root, self.directory)
            second = driver.seal(self.root, self.directory)
        self.assertEqual(first, second)
        self.assertEqual(first["original_item_count"], 1)
        self.assertEqual(first["trial_count"], 4)
        self.assertEqual(first["prompts"]["A1"], first["prompts"]["A2"])
        self.assertEqual(first["prompts"]["B1"], first["prompts"]["B2"])
        self.assertGreater(first["prompts"]["A1"]["bytes"], first["prompts"]["B1"]["bytes"])
        self.assertEqual(driver.checked(self.root, self.directory)["manifest_sha256"], first["manifest_sha256"])

    def test_preexisting_implementation_cannot_be_used_as_the_baseline(self):
        (self.root / driver.CODE).parent.mkdir(parents=True, exist_ok=True)
        (self.root / driver.CODE).write_text("already implemented")
        with self.assertRaisesRegex(ValueError, "without_implementation"):
            driver.seal(self.root, self.directory)

    def test_manifest_and_independent_evaluator_are_immutable(self):
        driver.seal(self.root, self.directory)
        (self.root / driver.EVAL).write_text("changed evaluator")
        with self.assertRaisesRegex(ValueError, "sealed_source_changed"):
            driver.checked(self.root, self.directory)
        path = self.directory / "sealed-manifest.json"
        value = json.loads(path.read_text(encoding="utf-8")); value["trial_count"] = 99
        driver.write(path, value)
        with self.assertRaisesRegex(ValueError, "manifest_changed"):
            driver.checked(self.root, self.directory)

    def test_task_conditions_differ_only_in_mode_and_receipt_identity(self):
        a = driver.task_body("A1", "repeat", "same fixed objective")
        b = driver.task_body("B1", "once", "same fixed objective")
        a.pop("task_id"); b.pop("task_id")
        a["execution"].pop("objective_mode"); b["execution"].pop("objective_mode")
        self.assertEqual(a, b)
        self.assertFalse(a["execution"]["allow_fallback"])
        self.assertFalse(a["execution"]["resume_session"])
        self.assertEqual(a["context_files"], [])

    def test_later_trial_cannot_start_before_independent_approval(self):
        driver.seal(self.root, self.directory)
        with patch.object(driver.Orchestrator, "run", side_effect=AssertionError("must not execute")):
            with self.assertRaisesRegex(ValueError, "earlier_trial_requires_independent_approval"):
                driver.run_trial(self.root, self.directory, "B1")

    def test_empty_results_do_not_report_a_saving(self):
        driver.seal(self.root, self.directory)
        result = driver.report_trials(self.root, self.directory)
        self.assertTrue(all(p["token_reduction_pct"] is None for p in result["paired"]))
        self.assertTrue(all(not p["comparable"] for p in result["paired"]))

    def test_actual_prompt_receipt_keeps_hash_and_bytes_without_the_body(self):
        body = driver.validate(driver.task_body("A1", "once", "DO-NOT-STORE-PROMPT-BODY"), self.root)
        context = driver.pack_context(body, self.root)
        log = self.directory / "prompt-receipts/test.jsonl"
        provider = driver.FixedCodex(log)
        with patch.object(driver.CodexCLIProvider, "execute", return_value=None):
            provider.execute(body, context, self.root, lambda: None)
        receipt = json.loads(log.read_text(encoding="utf-8"))
        self.assertEqual(receipt["sha256"], driver.hashlib.sha256(driver.codex_prompt(body, context).encode()).hexdigest())
        self.assertTrue(receipt["duplicate_removed"])
        self.assertNotIn("DO-NOT-STORE-PROMPT-BODY", log.read_text(encoding="utf-8"))

    def test_independent_acceptance_rejects_constant_true_and_false_implementations(self):
        acceptance = Path(__file__).resolve().parent
        for constant in (True, False):
            with self.subTest(constant=constant):
                source = self.root / ("negative-" + str(constant))
                package = source / "budongi"; package.mkdir(parents=True)
                (package / "__init__.py").write_text("")
                payload = {"schema_version": "team_collection_validation_v1", "record_type": "facility", "valid": constant,
                           "counts": {"raw": 3, "accepted": 1, "excluded": 1, "rejected": 1}, "errors": []}
                (package / "team_package.py").write_text("def validate_package(root):\n return " + repr(payload) + "\n", encoding="utf-8")
                environment = dict(os.environ, PYTHONPATH=str(source), PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
                result = subprocess.run([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", str(acceptance),
                                         "-p", "test_team_package_acceptance.py"], cwd=self.root,
                                        env=environment, capture_output=True, timeout=60)
                self.assertEqual(result.returncode, 1)
                self.assertIn(b"FAILED", result.stderr)


if __name__ == "__main__":
    unittest.main()

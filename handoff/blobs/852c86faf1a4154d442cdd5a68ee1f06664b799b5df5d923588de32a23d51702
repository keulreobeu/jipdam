"""Current GMS policy acceptance. No server/key/budget or model requests."""
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from jipdam_harness.contracts import HarnessError, encode, digest
from jipdam_harness.execution import GMSProvider, ExecutionResult
from jipdam_harness.handoff import _git
from jipdam_harness.managed import ManagedStore, validate
from jipdam_harness.managed_cli import main
from jipdam_harness.orchestrator import Orchestrator


class DeferredGMSTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        _git(self.root, "init")
        _git(self.root, "config", "user.name", "Fixture")
        _git(self.root, "config", "user.email", "fixture@example.invalid")
        (self.root / "test.py").write_text("value = 1\n")
        (self.root / ".gitignore").write_text(".local_runtime/\n")
        _git(self.root, "add", "."); _git(self.root, "commit", "-m", "fixture")
        self.body = {"task_id": "TASK-POLICY", "objective": "Offline fixture",
                     "scope": {"allowed_paths": ["test.py"], "forbidden_paths": []},
                     "acceptance_criteria": ["AC"], "execution": {"preferred_provider": "mock", "max_attempts": 1},
                     "validation": [{"argv": ["git", "diff", "--check"], "acs": ["AC"]}]}

    def test_new_defaults_and_explicit_gms_preferred_fallback_refused(self):
        self.assertEqual(validate(self.body, self.root)["execution"]["fallback_provider"], "codex")
        for field in ("preferred_provider", "fallback_provider"):
            body = deepcopy(self.body); body["execution"][field] = "gms"
            with self.assertRaisesRegex(HarnessError, "DEFERRED_GMS"): validate(body, self.root)
        store = ManagedStore(self.root / ".local_runtime/state", self.root)
        store.create(self.body)
        with self.assertRaisesRegex(HarnessError, "DEFERRED_GMS"): store.configure("TASK-POLICY", provider="gms")

    def test_provider_and_native_probe_do_not_touch_network_keys_or_counter(self):
        with patch("jipdam_harness.execution.http.client.HTTPConnection") as network, patch("jipdam_harness.execution.prepare_work") as counter, patch("jipdam_harness.execution.LocalGMSWork") as work:
            self.assertEqual(GMSProvider().availability()["reason"], "DEFERRED_GMS")
            self.assertEqual(GMSProvider().execute({}, "", self.root, lambda: None).error, "DEFERRED_GMS")
            out = io.StringIO()
            with redirect_stdout(out): code = main(["codex-gms-check"], workspace=self.root)
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(out.getvalue())["error"], "DEFERRED_GMS")
            network.assert_not_called(); counter.assert_not_called(); work.assert_not_called()

    def test_legacy_task_and_quota_fallback_are_stopped_before_invocation(self):
        for preferred in ("gms", "codex"):
            with self.subTest(preferred=preferred):
                store = ManagedStore(self.root / (".local_runtime/" + preferred), self.root)
                body = deepcopy(self.body)
                body["execution"].update(preferred_provider=preferred, fallback_provider="gms", allow_fallback=True)
                # Historical DB contents are preserved; production validation remains closed.
                with patch("jipdam_harness.provider_policy.GMS_DEFERRED", False): store.create(body)
                class Quota:
                    def execute(inner, *args): return ExecutionResult("error", "quota")
                class Never:
                    def execute(inner, *args): raise AssertionError("GMS called")
                with patch("jipdam_harness.execution.http.client.HTTPConnection") as network:
                    result = Orchestrator(store, {"codex": Quota(), "gms": Never()}).run("TASK-POLICY")
                self.assertEqual(result["state"], "WAITING_FOR_PROVIDER")
                self.assertEqual(result["result"]["reason"], "DEFERRED_GMS")
                self.assertEqual(store.get("TASK-POLICY")["task"]["execution"]["fallback_provider"], "gms")
                network.assert_not_called()

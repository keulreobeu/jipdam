"""Offline acceptance for the supplied fifteen wiki lifecycle scenarios."""
from copy import deepcopy
from datetime import timedelta
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from jipdam_harness.contracts import HarnessError
from jipdam_harness.managed_cli import main
from jipdam_harness.wiki import Wiki
from jipdam_harness.wiki_contracts import date, now, sha


class WikiLifecycleTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.source = self.root / "docs/operations.md"
        self.source.parent.mkdir()
        self.source.write_text("# Operating contract\n\nVerified procedure for the offline fixture.\n", encoding="utf-8")
        self.wiki = Wiki(self.root)
        self.counter = 0

    def event(self, **changes):
        self.counter += 1
        event = {"event_id": "EVENT-" + str(self.counter), "event_type": "task_verified", "task_id": "TASK-FIX",
                 "verified": True, "validation_passed": True, "reasons": ["explicit_request"],
                 "knowledge": {"key": "OPERATIONS", "title": "Verified operating guide", "project": "jipdam", "module": "harness",
                               "owner": "operator", "environment": "offline", "version": "1", "kind": "guide", "risk": "low",
                               "sections": {"purpose": "Repeatable operating procedure", "situation": "Fixture problem",
                                            "cause": "Confirmed ordering dependency; no remaining unknown cause",
                                            "procedure": "Follow the verified ordering in the source contract.",
                                            "cautions": "Only the offline fixture environment", "verification": "Offline fixture acceptance passed",
                                            "references": "docs/operations.md"},
                               "sources": [{"path": "docs/operations.md", "sha256": sha(self.source)}]},
                 "review": {"reviewer": "agent-codex", "evidence_checked": True, "semantic_checked": True,
                            "catalog_hash": self.wiki.catalog()["hash"], "independent_topic": True}}
        event.update(changes)
        return event

    def create(self, **changes):
        event = self.event()
        event["knowledge"].update(changes)
        result = self.wiki.process(event)
        return result["documents"][0]

    def page(self, doc):
        with self.wiki.tx() as c:
            return self.wiki._page(c, doc)

    def transition(self, doc, state, **changes):
        p = self.page(doc)
        request = {"document_id": doc, "status": state, "expected_revision": p["revision"], "reason": "verified lifecycle change",
                   "reviewer": "operator", "approved_by": "operator", "support_checked": True,
                   "still_supported": False, "retention_checked": True}
        request.update(changes)
        return self.wiki.transition(request)

    def test_typo_skip_and_unverified_review(self):
        r = self.wiki.process(self.event(reasons=[], exclude="typo"))
        self.assertEqual(r["action"], "SKIP")
        self.assertEqual(self.wiki.process(self.event(verified=False))["action"], "REVIEW_REQUIRED")
        self.assertEqual(self.wiki.search()["documents"], [])

    def test_second_same_cause_creates_then_updates(self):
        e = self.event(reasons=["repeated_problem"])
        e["knowledge"]["cause_key"] = "ORDERING"
        self.assertEqual(self.wiki.process(e)["action"], "SKIP")
        e = self.event(reasons=["repeated_problem"])
        e["knowledge"]["cause_key"] = "ORDERING"
        r = self.wiki.process(e)
        self.assertEqual(r["action"], "CREATE")
        doc = r["documents"][0]
        e = self.event(reasons=["repeated_problem"], expected_revision=1)
        e["knowledge"]["cause_key"] = "ORDERING"
        e["knowledge"]["sections"]["procedure"] += " Verified fallback."
        r = self.wiki.process(e)
        self.assertEqual(r["action"], "UPDATE")
        self.assertEqual(r["documents"], [doc])

    def test_schema_or_runbook_update_and_link_existing(self):
        doc = self.create()
        self.assertEqual(self.wiki.process(self.event())["action"], "LINK_EXISTING")
        for reason in ("contract_changed", "operations_changed"):
            e = self.event(reasons=[reason], expected_revision=self.page(doc)["revision"])
            e["knowledge"]["sections"]["procedure"] += reason
            r = self.wiki.process(e)
            self.assertEqual(r["action"], "UPDATE")
            self.assertEqual(r["documents"], [doc])
        self.assertEqual(len(self.wiki.history(doc)), 3)

    def test_temporary_owner_and_expiry_required(self):
        e = self.event()
        e["knowledge"]["kind"] = "temporary"
        self.assertEqual(self.wiki.process(e)["action"], "REVIEW_REQUIRED")
        doc = self.create(kind="temporary", expires_at=(date(now()) + timedelta(days=10)).isoformat())
        self.assertEqual(self.page(doc)["status"], "ACTIVE")
        e = self.event()
        e["knowledge"].update(kind="temporary", expires_at=(date(now()) + timedelta(days=31)).isoformat())
        self.assertEqual(self.wiki.process(e)["action"], "REVIEW_REQUIRED")

    def test_sensitive_input_never_persisted_and_exposure_quarantined(self):
        e = self.event()
        secret = "sk-" + "fixture_sensitive_token"
        e["knowledge"]["sections"]["procedure"] = secret
        with self.assertRaises(HarnessError): self.wiki.process(e)
        self.assertNotIn(secret.encode(), self.wiki.database.read_bytes())
        doc = self.create()
        path = self.wiki._path(doc)
        path.write_text(path.read_text(encoding="utf-8") + secret, encoding="utf-8")
        self.assertEqual(self.wiki.search()["documents"], [])
        self.wiki.maintain()
        self.assertNotIn(secret, path.read_text(encoding="utf-8"))
        self.assertEqual(self.page(doc)["status"], "REVIEW_REQUIRED")

    def test_manual_edits_and_parallel_revision_conflicts_preserved(self):
        doc = self.create()
        first = self.event(expected_revision=1)
        second = self.event(expected_revision=1)
        first["knowledge"]["sections"]["procedure"] = "Updated verified procedure."
        second["knowledge"]["sections"]["procedure"] = "Different competing procedure."
        self.wiki.process(first)
        second["review"]["catalog_hash"] = self.wiki.catalog()["hash"]
        self.assertEqual(self.wiki.process(second)["action"], "REVIEW_REQUIRED")
        path = self.wiki._path(doc)
        text = path.read_text(encoding="utf-8") + "\nManually authored note\n"
        path.write_text(text, encoding="utf-8")
        e = self.event(expected_revision=2)
        e["knowledge"]["sections"]["procedure"] = "Another proposal"
        self.assertEqual(self.wiki.process(e)["reason"], "wiki_manual_edit_conflict")
        self.assertEqual(path.read_text(encoding="utf-8"), text)
        self.wiki.maintain()
        self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_reviewer_catalog_and_source_fingerprints_required(self):
        for flag in ("evidence_checked", "semantic_checked"):
            e = self.event(); e["review"][flag] = False
            self.assertEqual(self.wiki.process(e)["action"], "REVIEW_REQUIRED")
        e = self.event(); self.source.write_text("Changed contract", encoding="utf-8")
        self.assertIn("source_changed", self.wiki.process(e)["reason"])
        e = self.event(); (self.root / "outputs/budongi_mvp_temp/docs/wiki/manual.md").write_text("existing knowledge")
        self.assertEqual(self.wiki.process(e)["action"], "REVIEW_REQUIRED")

    def test_core_risk_requires_publication_approval(self):
        doc = self.create(risk="recovery", kind="runbook")
        self.assertEqual(self.page(doc)["status"], "DRAFT")
        self.assertEqual(self.wiki.search()["documents"], [])
        e = self.event(expected_revision=1)
        e["knowledge"].update(risk="recovery", kind="runbook")
        e["review"]["publication_approved"] = True
        e["review"].update(publication_approved_by="operator", approval_ref="explicit fixture owner approval")
        self.assertFalse(self.wiki.process(e)["blocking"])
        self.assertEqual(self.page(doc)["status"], "ACTIVE")

    def test_review_due_stale_without_deletion(self):
        doc = self.create()
        future = (date(now()) + timedelta(days=181)).isoformat()
        with patch("jipdam_harness.wiki.now", return_value=future):
            r = self.wiki.maintain()
            self.assertEqual(r["outcomes"][0]["action"], "MARK_STALE")
            self.assertEqual(self.wiki.search()["documents"], [])
        self.assertTrue(self.wiki._path(doc).is_file())
        self.assertEqual(self.page(doc)["status"], "STALE")

    def test_source_changed_invalidates_search_before_maintenance(self):
        doc = self.create()
        self.source.write_text("New schema", encoding="utf-8")
        self.assertEqual(self.wiki.search()["documents"], [])
        self.wiki.maintain()
        self.assertEqual(self.page(doc)["status"], "STALE")

    def test_broken_local_and_unverified_remote_links_block_publication(self):
        e = self.event()
        e["knowledge"]["sections"]["references"] = "[missing](missing.md)"
        self.assertIn("broken_link", self.wiki.process(e)["reason"])
        e = self.event()
        e["knowledge"]["sections"]["references"] = "[source](https://example.invalid/contract)"
        self.assertIn("remote_link_unverified", self.wiki.process(e)["reason"])

    def test_merge_three_documents_and_preserve_old_versions(self):
        docs = [self.create(key="TOPIC" + str(i), title="Independent topic " + str(i)) for i in range(3)]
        request = {"document_id": docs[0], "duplicates": docs[1:], "approved_by": "operator", "reviewer": "operator",
                   "all_valid_content_preserved": True, "catalog_hash": self.wiki.catalog()["hash"],
                   "revisions": {d: 1 for d in docs[1:]}}
        self.assertEqual(self.wiki.merge(request)["action"], "MERGE")
        self.assertEqual(len(self.wiki.search()["documents"]), 1)
        self.assertEqual(self.page(docs[1])["replacement"], docs[0])
        old = self.create(key="TOPIC0", version="0")
        request.update(duplicates=[old], revisions={old: 1}, catalog_hash=self.wiki.catalog()["hash"])
        with self.assertRaisesRegex(HarnessError, "supported_version"): self.wiki.merge(request)
        self.assertEqual(self.page(old)["status"], "ACTIVE")

    def test_deprecate_archive_trash_and_support_guard(self):
        doc = self.create()
        with self.assertRaisesRegex(HarnessError, "support_and_retention"):
            self.transition(doc, "DEPRECATED", still_supported=True)
        self.transition(doc, "DEPRECATED")
        self.transition(doc, "ARCHIVED")
        self.transition(doc, "TRASHED")
        self.assertTrue(self.wiki._path(doc).exists())
        self.assertEqual(self.wiki.search()["documents"], [])
        with self.assertRaises(HarnessError): self.wiki.search(status="TRASHED")
        self.assertEqual(len(self.wiki.search(status="TRASHED", environment="offline", version="1")["documents"]), 1)

    def test_event_idempotence_and_restart(self):
        e = self.event(); r = self.wiki.process(e)
        self.assertEqual(self.wiki.process(e), r)
        reopened = Wiki(self.root)
        self.assertEqual(reopened.process(e), r)
        e["knowledge"]["title"] = "different"
        with self.assertRaisesRegex(HarnessError, "event_id_conflict"): reopened.process(e)
        self.assertEqual(len(reopened.catalog()["documents"]), 1)

    def test_connector_failure_pending_bounded_retry_and_receipt(self):
        self.wiki.configure({"target": "https://example.invalid/wiki", "visibility": "internal", "publish_authorized": True, "approved_by": "operator"})
        e = self.event(); r = self.wiki.process(e)
        self.assertTrue(r["blocking"])
        self.assertEqual(r["execution"], "SYNC_PENDING")
        item = next(i for i in self.wiki.pending() if i["channel"] == "wiki")
        self.assertIn("body", self.wiki.delivery(item["id"]))
        for _ in range(3):
            self.wiki.receipt({"delivery_id": item["id"], "success": False})
        with self.assertRaisesRegex(HarnessError, "retry_exhausted"):
            self.wiki.receipt({"delivery_id": item["id"], "success": False})
        self.wiki.receipt({"delivery_id": item["id"], "success": True, "reviewer": "operator", "remote_version": "1", "remote_hash": "a" * 64, "url": "https://example.invalid/wiki/pages/1"})
        self.assertFalse(self.wiki.decision(e["event_id"])["blocking"])

    def test_stale_delivery_cannot_acknowledge_new_revision(self):
        self.wiki.configure({"target": "https://example.invalid/wiki", "visibility": "internal", "publish_authorized": True, "approved_by": "operator"})
        doc = self.create()
        item = next(i for i in self.wiki.pending() if i["channel"] == "wiki")
        e = self.event(expected_revision=1); e["knowledge"]["sections"]["procedure"] += " Changed."
        self.wiki.process(e)
        with self.assertRaisesRegex(HarnessError, "revision_stale"):
            self.wiki.receipt({"delivery_id": item["id"], "success": True})
        self.assertEqual(self.page(doc)["revision"], 2)

    def test_no_external_authority_does_not_enqueue_publication(self):
        with self.assertRaisesRegex(HarnessError, "approval_required"):
            self.wiki.configure({"target": "https://example.invalid/wiki", "visibility": "public"})
        self.create()
        self.assertFalse(any(i["channel"] == "wiki" for i in self.wiki.pending()))

    def test_export_failure_is_pending_and_recoverable(self):
        e = self.event()
        with patch.object(self.wiki, "_export", side_effect=OSError()):
            self.assertEqual(self.wiki.process(e)["execution"], "SYNC_PENDING")
        self.assertEqual(self.wiki.search()["documents"], [])
        self.assertEqual(self.wiki.retry()["done"], 1)
        self.assertFalse(self.wiki.decision(e["event_id"])["blocking"])

    def test_cli_and_metrics(self):
        output = io.StringIO()
        with redirect_stdout(output):
            rc = main(["wiki", "catalog"], workspace=self.root)
        self.assertEqual(rc, 0)
        self.assertTrue(json.loads(output.getvalue())["complete"])
        self.create()
        self.assertEqual(self.wiki.metrics()["documents"]["ACTIVE"], 1)
        self.assertEqual(self.wiki.metrics()["model_calls"], 0)

    def test_resolution_must_match_task(self):
        e = self.event(verified=False); self.wiki.process(e)
        fix = self.event(resolves=e["event_id"], task_id="TASK-OTHER")
        with self.assertRaisesRegex(HarnessError, "task_mismatch"): self.wiki.process(fix)
        fix = self.event(resolves=e["event_id"])
        self.wiki.process(fix)
        self.assertFalse(self.wiki.decision(e["event_id"])["blocking"])

    def test_managed_verification_hook_and_completion_gate(self):
        from jipdam_harness.isolation import git
        from jipdam_harness.managed import ManagedStore
        from jipdam_harness.orchestrator import Orchestrator
        from jipdam_harness.execution import ExecutionResult
        policy = self.root / "outputs/budongi_mvp_temp/docs/wiki/LIFECYCLE_POLICY.md"
        policy.write_text("Explicitly enabled wiki policy for the offline fixture", encoding="utf-8")
        (self.root / ".gitignore").write_text(".local_runtime/\n__pycache__/\n", encoding="utf-8")
        git(self.root, "init"); git(self.root, "config", "user.email", "offline@example.invalid")
        git(self.root, "config", "user.name", "Offline fixture")
        git(self.root, "add", "."); git(self.root, "commit", "-m", "offline fixture")
        store = ManagedStore(self.root / ".local_runtime/harness-managed", self.root)
        task = {"task_id": "TASK-AUTOMATIC", "objective": "Verify a changed operating contract",
                "scope": {"allowed_paths": ["docs"]}, "acceptance_criteria": ["AC1"],
                "validation": [{"argv": ["git", "diff", "--check"], "acs": ["AC1"]}],
                "execution": {"preferred_provider": "mock"}, "safety": {"require_approval": False}}
        store.create(task)
        class Provider:
            def execute(self, task, context, cwd, stop):
                (cwd / "docs/operations.md").write_text("Updated operating contract\n", encoding="utf-8")
                return ExecutionResult()
        row = Orchestrator(store, {"mock": Provider()}).run("TASK-AUTOMATIC")
        self.assertEqual(row["state"], "REVIEW_REQUIRED")
        self.assertEqual(row["result"]["wiki"]["action"], "REVIEW_REQUIRED")
        with self.assertRaisesRegex(HarnessError, "wiki_review_required"):
            store.approve("TASK-AUTOMATIC", "operator")
        event = self.event(resolves=row["result"]["wiki"]["event_id"], task_id="TASK-AUTOMATIC",
                           reasons=[], exclude="refactor_only")
        self.wiki.process(event)
        self.assertEqual(store.approve("TASK-AUTOMATIC", "operator")["state"], "COMPLETED")

    def test_path_escape_and_inbound_references(self):
        e = self.event()
        e["knowledge"]["sources"] = [{"path": "../outside.md", "sha256": "a" * 64}]
        self.assertEqual(self.wiki.process(e)["action"], "REVIEW_REQUIRED")
        doc = self.create()
        (self.root / "docs/references.md").write_text("[guide](" + doc + ".md)", encoding="utf-8")
        self.transition(doc, "DEPRECATED")
        with self.assertRaisesRegex(HarnessError, "inbound_references"):
            self.transition(doc, "ARCHIVED")

    def test_teammate_permission_failure_has_actionable_request_guidance(self):
        self.wiki.configure({"target": "https://example.invalid/wiki", "visibility": "internal", "publish_authorized": True, "approved_by": "operator"})
        self.create()
        item = next(i for i in self.wiki.pending() if i["channel"] == "wiki")
        self.assertIn("permission_guidance", self.wiki.delivery(item["id"]))
        result = self.wiki.receipt({"delivery_id": item["id"], "success": False, "failure_kind": "permission"})
        self.assertEqual(result["status"], "SYNC_PENDING")
        self.assertEqual(result["guidance"]["target"], "https://example.invalid/wiki")
        self.assertEqual(next(i for i in self.wiki.pending() if i["id"] == item["id"])["error"], "permission_required")
        self.wiki.retry(channel="wiki")
        self.assertEqual(next(i for i in self.wiki.pending() if i["id"] == item["id"])["attempts"], 1)

    def test_remote_readback_hash_preserves_content_and_normalizes_line_endings(self):
        from jipdam_harness.wiki_contracts import remote_hash
        self.assertEqual(remote_hash("<p>Same</p>"), remote_hash("<p>Same</p>\r\n"))
        self.assertNotEqual(remote_hash("<p>Same</p>"), remote_hash("<p>Manual edit</p>"))
        path = self.root / ".local_runtime/readback.html"
        path.write_text("<p>Saved remote content</p>", encoding="utf-8")
        output = io.StringIO()
        with redirect_stdout(output):
            rc = main(["wiki", "remote-hash", "--file", ".local_runtime/readback.html"], workspace=self.root)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(output.getvalue())["remote_hash"], remote_hash(path.read_text(encoding="utf-8")))

    def test_teammate_clone_rebuilds_catalog_without_runtime_database(self):
        import shutil
        doc = self.create()
        clone = self.root / "teammate"
        (clone / "docs").mkdir(parents=True)
        shutil.copy2(self.source, clone / "docs/operations.md")
        pages = clone / "outputs/budongi_mvp_temp/docs/wiki/pages"
        pages.mkdir(parents=True)
        shutil.copy2(self.wiki._path(doc), pages / (doc + ".md"))
        teammate = Wiki(clone)
        self.assertEqual(teammate.search()["documents"][0]["id"], doc)
        event = self.event()
        event["review"]["catalog_hash"] = teammate.catalog()["hash"]
        self.assertEqual(teammate.process(event)["action"], "LINK_EXISTING")

    def test_unreviewed_shared_manual_change_does_not_become_active_on_clone(self):
        import shutil
        doc = self.create()
        clone = self.root / "teammate"
        (clone / "docs").mkdir(parents=True)
        shutil.copy2(self.source, clone / "docs/operations.md")
        pages = clone / "outputs/budongi_mvp_temp/docs/wiki/pages"
        pages.mkdir(parents=True)
        text = self.wiki._path(doc).read_text(encoding="utf-8") + "Unreviewed manual addition\n"
        (pages / (doc + ".md")).write_text(text, encoding="utf-8")
        teammate = Wiki(clone)
        self.assertEqual(teammate.search()["documents"], [])
        self.assertEqual(teammate.pending()[0]["channel"], "review")


if __name__ == "__main__":
    unittest.main()

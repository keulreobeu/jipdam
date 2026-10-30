import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.package.validation_doc import (
    REJECTED_LIMIT, build_validation, reconcile)


def sec(name, raw, a, e, r):
    return {"section": name, "raw": raw, "accepted": a, "excluded": e, "rejected": r}


def base_stats():
    return {
        "lane": "A1",
        "sections": [sec("s1", 3, 1, 1, 1), sec("s2", 2, 2, 0, 0)],
        "jsonl_lines": 4,
        "source_id": "seoul_bus",
        "batch_id": "seoul-bus-20261029-v1",
        "mapping_version": "m1",
        "validated_at_utc": "2026-10-29T01:02:03Z",
        "parser": {"commit": "abc"},
        "rejected_rows": [{"section": "s1", "position": 7, "reason": "missing_required:name"}],
        "excluded_reasons": ["blank_row"],
    }


class VisibleReconcileTest(unittest.TestCase):
    def test_clean_counts_reconcile_to_empty_list(self):
        self.assertEqual(reconcile(base_stats()), [])

    def test_raw_mismatch_names_section(self):
        s = base_stats()
        s["sections"][0]["raw"] = 4
        self.assertEqual(reconcile(s), ["raw_mismatch:s1"])

    def test_api_lane_expected_backfilled(self):
        s = {"lane": "B", "sections": [sec("s", 2, 2, 0, 0)], "jsonl_lines": 2,
             "requests": [{"request_id": "r1", "section": "s", "received_rows": 2,
                           "expected_rows": 2, "expected_basis": None}]}
        self.assertEqual(reconcile(s), ["expected_backfilled:r1"])

    def test_invalid_lane_raises(self):
        with self.assertRaises(C.ContractError) as cm:
            reconcile({"lane": "Z", "sections": [], "jsonl_lines": 0})
        self.assertEqual(str(cm.exception), "invalid_stats:lane")


class VisibleBuildValidationTest(unittest.TestCase):
    def test_document_header_and_reconciliation(self):
        doc = build_validation(base_stats())
        self.assertEqual(doc["delivery_schema_version"], C.DELIVERY_SCHEMA_VERSION)
        self.assertEqual(doc["source_id"], "seoul_bus")
        self.assertEqual(doc["batch_id"], "seoul-bus-20261029-v1")
        self.assertEqual(doc["validated_at_utc"], "2026-10-29T01:02:03Z")
        self.assertEqual(doc["parser"], {"commit": "abc"})
        rec = doc["reconciliation"]
        self.assertEqual((rec["raw"], rec["accepted"], rec["excluded"], rec["rejected"]),
                         (5, 3, 1, 1))
        self.assertTrue(rec["rows_equal_accepted_plus_excluded_plus_rejected"])
        self.assertTrue(rec["ok"])
        self.assertEqual(doc["errors"], [])

    def test_sections_rejected_and_excluded(self):
        doc = build_validation(base_stats())
        self.assertEqual(doc["sections"][0],
                         {"section": "s1", "raw": 3, "accepted": 1, "excluded": 1,
                          "rejected": 1, "equal": True})
        self.assertEqual(doc["rejected"], {"total": 1, "truncated": False, "items": [
            {"section": "s1", "position": 7, "reason": "missing_required:name"}]})
        self.assertEqual(doc["excluded_by_reason"], {"blank_row": 1})
        self.assertEqual(REJECTED_LIMIT, 200)

    def test_errors_reported_not_raised(self):
        s = base_stats()
        s["jsonl_lines"] = 9
        doc = build_validation(s)
        self.assertEqual(doc["errors"], ["jsonl_mismatch"])
        self.assertFalse(doc["reconciliation"]["ok"])


if __name__ == "__main__":
    unittest.main()

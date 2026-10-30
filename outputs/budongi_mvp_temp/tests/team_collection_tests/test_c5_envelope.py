"""Visible tests for C5 core/envelope.py (typical paths)."""
from __future__ import annotations

import dataclasses
import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.core.envelope import (
    BatchContext,
    finalize,
    make_envelope,
    validate_envelope,
)

SHA = "a" * 64


def ctx(**over) -> BatchContext:
    base = dict(source_id="seoul_lib", batch_id="seoul-lib-20261029-v1", mapping_version="m1",
                record_type="facility", staged_at_utc="2026-10-29T00:00:00Z")
    base.update(over)
    return BatchContext(**base)


def env(**over) -> dict:
    kw = dict(file_ref="raw/a.csv", file_sha=SHA, section="main", position=3)
    kw.update(over)
    return make_envelope(ctx(), **kw)


class C5VisibleContextTests(unittest.TestCase):
    def test_defaults_and_frozen(self):
        c = ctx()
        self.assertIsNone(c.source_retrieved_at_utc)
        self.assertIsNone(c.provided_at_utc)
        self.assertIsNone(c.source_date)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            c.source_id = "other"


class C5VisibleMakeTests(unittest.TestCase):
    def test_keys_exact(self):
        self.assertEqual(set(env()), set(C.ENVELOPE_FIELDS + C.LOCATION_FIELDS))

    def test_values_filled(self):
        e = make_envelope(ctx(source_retrieved_at_utc="2026-10-28T01:02:03Z", source_date="2026-10-01"),
                          file_ref="raw/a.csv", file_sha=SHA, section="main", position=3, column=2)
        self.assertEqual(e["delivery_schema_version"], C.DELIVERY_SCHEMA_VERSION)
        self.assertEqual(e["quality_status"], C.QUALITY_STATUS)
        self.assertEqual(e["source_id"], "seoul_lib")
        self.assertEqual(e["source_file_ref"], "raw/a.csv")
        self.assertEqual(e["source_content_sha256"], SHA)
        self.assertEqual(e["source_section"], "main")
        self.assertEqual(e["source_row_number"], 3)
        self.assertEqual(e["source_column_number"], 2)
        self.assertIsNone(e["source_feature_id"])
        self.assertEqual(e["source_retrieved_at_utc"], "2026-10-28T01:02:03Z")
        self.assertEqual(e["source_date"], "2026-10-01")
        self.assertIsNone(e["validation_status"])
        self.assertIsNone(e["latitude"])

    def test_feature_id(self):
        e = env(position=None, feature_id="F1")
        self.assertEqual(e["source_feature_id"], "F1")
        self.assertIsNone(e["source_row_number"])

    def test_no_position_raises(self):
        with self.assertRaises(C.ContractError) as cm:
            env(position=None)
        self.assertEqual(str(cm.exception), "invalid_position")

    def test_bad_sha_raises(self):
        with self.assertRaises(C.ContractError) as cm:
            env(file_sha="A" * 64)
        self.assertEqual(str(cm.exception), "invalid_sha256")


class C5VisibleFinalizeTests(unittest.TestCase):
    def test_rejected_with_detail(self):
        out = finalize(env(), "rejected", "missing_required:name")
        self.assertEqual(out["validation_status"], "rejected")
        self.assertEqual(out["validation_reason"], "missing_required:name")

    def test_accepted(self):
        out = finalize(env(), "accepted")
        self.assertEqual(out["validation_status"], "accepted")
        self.assertIsNone(out["validation_reason"])

    def test_reason_forbidden(self):
        with self.assertRaises(C.ContractError) as cm:
            finalize(env(), "accepted", "blank_row")
        self.assertEqual(str(cm.exception), "reason_forbidden")

    def test_mismatch(self):
        with self.assertRaises(C.ContractError) as cm:
            finalize(env(), "rejected", "blank_row")
        self.assertEqual(str(cm.exception), "reason_status_mismatch")


class C5VisibleValidateTests(unittest.TestCase):
    def test_not_finalized(self):
        self.assertEqual(validate_envelope(env()), ["not_finalized"])

    def test_valid(self):
        self.assertEqual(validate_envelope(finalize(env(), "excluded", "blank_row")), [])

    def test_bad_sha_and_utc(self):
        rec = finalize(env(), "accepted")
        rec["source_content_sha256"] = "xyz"
        rec["staged_at_utc"] = "2026-10-29 00:00:00"
        codes = validate_envelope(rec)
        self.assertIn("invalid_sha256", codes)
        self.assertIn("invalid_utc:staged_at_utc", codes)

    def test_not_a_dict(self):
        self.assertEqual(validate_envelope([]), ["not_a_dict"])


if __name__ == "__main__":
    unittest.main()

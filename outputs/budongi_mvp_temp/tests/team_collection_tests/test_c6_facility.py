"""Visible tests for C6 normalize/facility.py (typical paths)."""
from __future__ import annotations

import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome
from budongi.team_collection.normalize.facility import normalize_facility


def make_env() -> dict:
    env = {key: None for key in C.ENVELOPE_FIELDS + C.LOCATION_FIELDS}
    env.update({
        "delivery_schema_version": C.DELIVERY_SCHEMA_VERSION,
        "quality_status": C.QUALITY_STATUS,
        "source_id": "seoul_library",
        "batch_id": "seoul-library-20261029-v1",
        "mapping_version": "m1",
        "record_type": "facility",
        "source_file_ref": "raw/library.csv",
        "source_content_sha256": "a" * 64,
        "source_section": "main",
        "source_row_number": 1,
        "staged_at_utc": "2026-10-29T00:00:00Z",
    })
    return env


class TestNormalizeFacility(unittest.TestCase):
    def test_accepted_with_raw_type(self):
        env = make_env()
        out = normalize_facility(
            {"name": "Seoul Library", "facility_type_raw": "L01", "source_entity_id": "X1"},
            envelope=env, type_namespace="seoul_lib")
        self.assertIsInstance(out, Outcome)
        self.assertEqual(out.status, "accepted")
        self.assertIsNone(out.reason)
        rec = out.record
        self.assertEqual(rec["facility_type_code"], "seoul_lib:L01")
        self.assertEqual(rec["entity_level"], "facility")
        self.assertEqual(rec["name"], "Seoul Library")
        self.assertEqual(rec["facility_type_raw"], "L01")
        self.assertEqual(rec["source_entity_id"], "X1")
        self.assertEqual(rec["source_id"], "seoul_library")
        self.assertEqual(rec["validation_status"], "accepted")
        self.assertIsNone(rec["validation_reason"])

    def test_accepted_with_code_only(self):
        out = normalize_facility({"name": "Seoul Library", "facility_type_code": "library"},
                                 envelope=make_env(), type_namespace="seoul_lib")
        self.assertEqual(out.status, "accepted")
        self.assertEqual(out.record["facility_type_code"], "library")
        self.assertEqual(out.record["entity_level"], "facility")

    def test_rejected_missing_name(self):
        out = normalize_facility({"facility_type_raw": "L01"},
                                 envelope=make_env(), type_namespace="seoul_lib")
        self.assertIsInstance(out, Outcome)
        self.assertEqual(out.status, "rejected")
        self.assertEqual(out.reason, "missing_required:name")
        self.assertEqual(out.record["validation_status"], "rejected")
        self.assertEqual(out.record["validation_reason"], "missing_required:name")
        self.assertEqual(out.record["facility_type_code"], "seoul_lib:L01")

    def test_rejected_missing_type_code(self):
        out = normalize_facility({"name": "X"}, envelope=make_env(), type_namespace="ns")
        self.assertEqual(out.status, "rejected")
        self.assertEqual(out.reason, "missing_required:facility_type_code")
        self.assertIsNone(out.record["facility_type_code"])

    def test_leading_zero_raw_kept(self):
        out = normalize_facility({"name": "X", "facility_type_raw": "01"},
                                 envelope=make_env(), type_namespace="ns")
        self.assertEqual(out.record["facility_type_code"], "ns:01")

    def test_empty_namespace_raises(self):
        with self.assertRaises(C.ContractError) as ctx:
            normalize_facility({"name": "X", "facility_type_raw": "A"},
                               envelope=make_env(), type_namespace="")
        self.assertEqual(str(ctx.exception), "invalid_namespace")


if __name__ == "__main__":
    unittest.main()

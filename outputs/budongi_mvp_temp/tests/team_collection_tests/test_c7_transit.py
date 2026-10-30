"""Visible tests for C7 normalize/transit.py (typical paths)."""
from __future__ import annotations

import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome
from budongi.team_collection.normalize.transit import normalize_route, normalize_stop_link


def make_env(record_type: str = "transit_route") -> dict:
    env = {key: None for key in C.ENVELOPE_FIELDS + C.LOCATION_FIELDS}
    env.update({
        "delivery_schema_version": C.DELIVERY_SCHEMA_VERSION,
        "quality_status": C.QUALITY_STATUS,
        "source_id": "seoul_bus",
        "batch_id": "seoul-bus-20261029-v1",
        "mapping_version": "m1",
        "record_type": record_type,
        "source_file_ref": "raw/routes.csv",
        "source_content_sha256": "a" * 64,
        "source_section": "main",
        "source_row_number": 1,
        "staged_at_utc": "2026-10-29T00:00:00Z",
    })
    return env


class TestNormalizeRoute(unittest.TestCase):
    def test_accepted_route(self):
        out = normalize_route({"route_id": "100100118", "route_name": "6411"},
                              envelope=make_env(), namespace="seoul_bus")
        self.assertIsInstance(out, Outcome)
        self.assertEqual(out.status, "accepted")
        self.assertIsNone(out.reason)
        rec = out.record
        self.assertEqual(rec["identifier_namespace"], "seoul_bus")
        self.assertEqual(rec["source_entity_id"], "100100118")
        self.assertEqual(rec["name"], "6411")
        self.assertEqual(rec["entity_level"], "network")
        self.assertEqual(rec["route_id"], "100100118")
        self.assertEqual(rec["source_id"], "seoul_bus")
        self.assertEqual(rec["validation_status"], "accepted")
        self.assertIsNone(rec["validation_reason"])

    def test_missing_name_rejected(self):
        out = normalize_route({"route_id": "R1"}, envelope=make_env(), namespace="seoul_bus")
        self.assertEqual(out.status, "rejected")
        self.assertEqual(out.reason, "missing_required:name")
        self.assertEqual(out.record["validation_reason"], "missing_required:name")

    def test_blank_namespace_raises(self):
        with self.assertRaises(C.ContractError) as ctx:
            normalize_route({"route_id": "R1", "route_name": "N"},
                            envelope=make_env(), namespace=" ")
        self.assertEqual(str(ctx.exception), "invalid_namespace")


class TestNormalizeStopLink(unittest.TestCase):
    def _run(self, fields):
        return normalize_stop_link(fields, envelope=make_env("transit_stop_link"),
                                   route_namespace="seoul_bus", stop_namespace="seoul_ars")

    def test_accepted_link(self):
        out = self._run({"route_id": "R1", "stop_id": "01001", "stop_sequence": "12"})
        self.assertIsInstance(out, Outcome)
        self.assertEqual(out.status, "accepted")
        self.assertIsNone(out.reason)
        rec = out.record
        self.assertEqual(rec["route_namespace"], "seoul_bus")
        self.assertEqual(rec["source_route_id"], "R1")
        self.assertEqual(rec["stop_namespace"], "seoul_ars")
        self.assertEqual(rec["source_stop_id"], "01001")
        self.assertEqual(rec["stop_sequence"], 12)
        self.assertEqual(rec["entity_level"], "network")
        self.assertEqual(rec["validation_status"], "accepted")

    def test_int_sequence_zero(self):
        out = self._run({"route_id": "R1", "stop_id": "S1", "stop_sequence": 0})
        self.assertEqual(out.status, "accepted")
        self.assertEqual(out.record["stop_sequence"], 0)

    def test_negative_sequence_rejected(self):
        out = self._run({"route_id": "R1", "stop_id": "S1", "stop_sequence": "-1"})
        self.assertEqual(out.status, "rejected")
        self.assertEqual(out.reason, "invalid_sequence")
        self.assertIsNone(out.record["stop_sequence"])
        self.assertEqual(out.record["stop_sequence_raw"], "-1")

    def test_missing_stop_id_rejected(self):
        out = self._run({"route_id": "R1", "stop_sequence": "1"})
        self.assertEqual(out.reason, "missing_required:source_stop_id")


if __name__ == "__main__":
    unittest.main()

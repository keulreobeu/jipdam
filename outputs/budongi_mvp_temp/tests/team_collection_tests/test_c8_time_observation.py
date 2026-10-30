"""Visible tests for C8 normalize/time_observation.py (typical paths)."""
from __future__ import annotations

import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome
from budongi.team_collection.normalize.time_observation import normalize_observations

TS = "2026-10-29T00:00:00Z"
METRICS = [
    {"metric_code": "pm10", "source_field": "pm10", "unit_code": "ug_m3"},
    {"metric_code": "pm25", "source_field": "pm25", "unit_code": "ug_m3"},
]


def make_env() -> dict:
    env = {key: None for key in C.ENVELOPE_FIELDS + C.LOCATION_FIELDS}
    env.update({
        "delivery_schema_version": C.DELIVERY_SCHEMA_VERSION,
        "quality_status": C.QUALITY_STATUS,
        "source_id": "air_quality",
        "batch_id": "air-quality-20261029-v1",
        "mapping_version": "m1",
        "record_type": "time_observation",
        "source_file_ref": "raw/air.csv",
        "source_content_sha256": "c" * 64,
        "source_section": "main",
        "source_row_number": 1,
        "staged_at_utc": "2026-10-29T00:00:00Z",
    })
    return env


def run(fields, metrics=METRICS, ts=TS):
    return normalize_observations(fields, envelope=make_env(), metrics=metrics,
                                  subject_namespace="airkorea", subject_field="stn",
                                  observed_at_utc=ts)


class TestNormalizeObservations(unittest.TestCase):
    def test_numeric_and_missing(self):
        out = run({"stn": "108", "pm10": "42", "pm25": "-"})
        self.assertIsInstance(out, list)
        self.assertEqual(len(out), 2)
        for o in out:
            self.assertIsInstance(o, Outcome)
            self.assertEqual(o.status, "accepted")
            self.assertIsNone(o.reason)
        a, b = out[0].record, out[1].record
        self.assertEqual(a["metric_code"], "pm10")
        self.assertEqual(a["unit_code"], "ug_m3")
        self.assertEqual(a["subject_namespace"], "airkorea")
        self.assertEqual(a["source_subject_id"], "108")
        self.assertEqual(a["observed_at_utc"], TS)
        self.assertEqual(a["value_status"], "numeric")
        self.assertEqual(a["value_decimal"], "42")
        self.assertEqual(a["value_raw"], "42")
        self.assertEqual(a["source_id"], "air_quality")
        self.assertEqual(a["validation_status"], "accepted")
        self.assertIsNone(a["validation_reason"])
        self.assertEqual(b["metric_code"], "pm25")
        self.assertEqual(b["value_status"], "missing")
        self.assertIsNone(b["value_decimal"])
        self.assertEqual(b["value_raw"], "-")

    def test_decimal_text_normalized(self):
        out = run({"stn": "1", "pm10": " 1,234 ", "pm25": "12.50"})
        self.assertEqual(out[0].record["value_decimal"], "1234")
        self.assertEqual(out[1].record["value_decimal"], "12.50")

    def test_invalid_number_rejected(self):
        out = run({"stn": "108", "pm10": "abc", "pm25": "7"})
        self.assertEqual(out[0].status, "rejected")
        self.assertEqual(out[0].reason, "invalid_number:pm10")
        self.assertEqual(out[0].record["validation_reason"], "invalid_number:pm10")
        self.assertEqual(out[0].record["value_raw"], "abc")
        self.assertIsNone(out[0].record["value_decimal"])
        self.assertEqual(out[1].status, "accepted")

    def test_missing_subject_rejected(self):
        out = run({"pm10": "1", "pm25": "2"})
        for o in out:
            self.assertEqual(o.status, "rejected")
            self.assertEqual(o.reason, "missing_required:source_subject_id")
            self.assertIsNone(o.record["source_subject_id"])

    def test_empty_metrics_raises(self):
        with self.assertRaises(C.ContractError) as ctx:
            run({"stn": "1"}, metrics=[])
        self.assertEqual(str(ctx.exception), "invalid_metrics")

    def test_bad_timestamp_raises(self):
        with self.assertRaises(C.ContractError) as ctx:
            run({"stn": "1"}, ts="2026-10-29 00:00:00")
        self.assertEqual(str(ctx.exception), "invalid_observed_at")


if __name__ == "__main__":
    unittest.main()

"""Visible tests for C10 normalize/regional_statistic.py (typical paths)."""
from __future__ import annotations

import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome
from budongi.team_collection.normalize.regional_statistic import normalize_statistic


def make_env() -> dict:
    env = {key: None for key in C.ENVELOPE_FIELDS + C.LOCATION_FIELDS}
    env.update({
        "delivery_schema_version": C.DELIVERY_SCHEMA_VERSION,
        "quality_status": C.QUALITY_STATUS,
        "source_id": "seoul_stats",
        "batch_id": "seoul-stats-20261029-v1",
        "mapping_version": "m1",
        "record_type": "regional_statistic",
        "source_file_ref": "raw/stats.csv",
        "source_content_sha256": "a" * 64,
        "source_section": "main",
        "source_row_number": 1,
        "staged_at_utc": "2026-10-29T00:00:00Z",
    })
    return env


def run(fields, **kw):
    args = dict(envelope=make_env(), metric_code="trade_count", frequency="monthly",
                unit_code="count", value_field="cnt", region_fields=("sido", "sgg"),
                dimensions={})
    args.update(kw)
    return normalize_statistic(fields, **args)


BASE = {"sido": "서울특별시", "sgg": "강남구", "period_key": "2026-08", "cnt": "1,234"}


class TestNormalizeStatistic(unittest.TestCase):
    def test_accepted_numeric(self):
        out = run(dict(BASE))
        self.assertIsInstance(out, Outcome)
        self.assertEqual(out.status, "accepted")
        self.assertIsNone(out.reason)
        rec = out.record
        self.assertEqual(rec["region_path_raw"], "서울특별시 > 강남구")
        self.assertEqual(rec["value_status"], "numeric")
        self.assertEqual(rec["value_decimal"], "1234")
        self.assertEqual(rec["value_raw"], "1,234")
        self.assertEqual(rec["metric_code"], "trade_count")
        self.assertEqual(rec["frequency"], "monthly")
        self.assertEqual(rec["unit_code"], "count")
        self.assertEqual(rec["period_key"], "2026-08")
        self.assertEqual(rec["dimensions_json"], "{}")
        self.assertEqual(rec["source_id"], "seoul_stats")
        self.assertEqual(rec["sido"], "서울특별시")
        self.assertEqual(rec["validation_status"], "accepted")
        self.assertIsNone(rec["validation_reason"])

    def test_dimensions_canonical(self):
        out = run(dict(BASE), dimensions={"type": "apt", "area": "60"})
        self.assertEqual(out.record["dimensions_json"], '{"area":"60","type":"apt"}')

    def test_missing_value_accepted(self):
        out = run(dict(BASE, cnt="-"))
        self.assertEqual(out.status, "accepted")
        self.assertEqual(out.record["value_status"], "missing")
        self.assertIsNone(out.record["value_decimal"])

    def test_invalid_number(self):
        out = run(dict(BASE, cnt="abc"))
        self.assertEqual(out.status, "rejected")
        self.assertEqual(out.reason, "invalid_number:cnt")
        self.assertEqual(out.record["validation_reason"], "invalid_number:cnt")
        self.assertIsNone(out.record["value_status"])
        self.assertEqual(out.record["value_raw"], "abc")

    def test_missing_period(self):
        fields = dict(BASE)
        del fields["period_key"]
        out = run(fields)
        self.assertEqual(out.status, "rejected")
        self.assertEqual(out.reason, "missing_required:period_key")

    def test_bad_frequency(self):
        with self.assertRaises(C.ContractError) as ctx:
            run(dict(BASE), frequency="weekly")
        self.assertEqual(str(ctx.exception), "invalid_frequency")


if __name__ == "__main__":
    unittest.main()

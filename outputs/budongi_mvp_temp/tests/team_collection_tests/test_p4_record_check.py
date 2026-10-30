from __future__ import annotations

import json
import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.package.record_check import check_records

SHA = "a" * 64


def rec(**over):
    r = {k: None for k in C.ENVELOPE_FIELDS + C.LOCATION_FIELDS}
    r.update({
        "delivery_schema_version": C.DELIVERY_SCHEMA_VERSION,
        "quality_status": C.QUALITY_STATUS,
        "source_id": "s1", "batch_id": "b-20261029-v1", "mapping_version": "m1",
        "record_type": "facility", "source_file_ref": "raw/a.csv",
        "source_content_sha256": SHA, "source_section": "", "source_row_number": 1,
        "staged_at_utc": "2026-10-29T00:00:00Z",
        "validation_status": "accepted", "validation_reason": None,
        "entity_level": "facility", "name": "X", "facility_type_code": "ns:1",
    })
    r.update(over)
    return r


def man(accepted=1, rejected=0):
    return {"source_id": "s1", "batch_id": "b-20261029-v1", "mapping_version": "m1",
            "record_type": "facility",
            "counts": {"raw": accepted + rejected, "accepted": accepted,
                       "excluded": 0, "rejected": rejected}}


FILES = {"raw/a.csv": {"path": "raw/a.csv", "bytes": 3, "sha256": SHA}}


def run(records, **mk):
    lines = [r if isinstance(r, str) else json.dumps(r) for r in records]
    return check_records(lines, manifest=man(**mk), files=FILES)


class RecordCheckVisibleTests(unittest.TestCase):
    def test_valid_line_ok(self):
        res = run([rec()])
        self.assertEqual(res, {"ok": True, "errors": [],
                               "counts": {"lines": 1, "accepted": 1, "rejected": 0, "invalid": 0}})

    def test_rejected_line_counted(self):
        r = rec(validation_status="rejected", validation_reason="missing_required:name", name=None)
        res = run([r], accepted=0, rejected=1)
        self.assertTrue(res["ok"])
        self.assertEqual(res["counts"]["rejected"], 1)

    def test_invalid_json(self):
        res = run(["not json", rec()])
        self.assertEqual(res["errors"], ["invalid_json:1"])
        self.assertEqual(res["counts"], {"lines": 2, "accepted": 1, "rejected": 0, "invalid": 1})
        self.assertFalse(res["ok"])

    def test_excluded_in_jsonl(self):
        r = rec(validation_status="excluded", validation_reason="blank_row")
        res = run([r], accepted=0)
        self.assertEqual(res["errors"], ["excluded_in_jsonl:1"])

    def test_unknown_file_ref(self):
        res = run([rec(source_file_ref="raw/zzz.csv")])
        self.assertEqual(res["errors"], ["unknown_file_ref:1"])

    def test_duplicate_position(self):
        res = run([rec(), rec()], accepted=2)
        self.assertEqual(res["errors"], ["duplicate_position:2"])

    def test_missing_required(self):
        res = run([rec(name=None)])
        self.assertEqual(res["errors"], ["missing_required:1:name"])

    def test_coordinates(self):
        good = rec(latitude=37.5, longitude=127.0, source_crs=C.WGS84,
                   source_axis_order="x=lon,y=lat")
        self.assertTrue(run([good])["ok"])
        bad = dict(good, source_crs="EPSG:5179")
        self.assertEqual(run([bad])["errors"], ["coordinate_rule:1"])

    def test_accepted_count_mismatch(self):
        res = run([rec()], accepted=5)
        self.assertEqual(res["errors"], ["accepted_count_mismatch"])


if __name__ == "__main__":
    unittest.main()

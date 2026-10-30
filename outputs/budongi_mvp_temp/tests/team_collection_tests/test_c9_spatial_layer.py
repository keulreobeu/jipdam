"""Visible tests for C9 normalize/spatial_layer.py (typical paths)."""
from __future__ import annotations

import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome
from budongi.team_collection.normalize.spatial_layer import VERDICT_FIELDS, normalize_feature


def make_env() -> dict:
    env = {key: None for key in C.ENVELOPE_FIELDS + C.LOCATION_FIELDS}
    env.update({
        "delivery_schema_version": C.DELIVERY_SCHEMA_VERSION,
        "quality_status": C.QUALITY_STATUS,
        "source_id": "safemap_flood",
        "batch_id": "safemap-flood-20261029-v1",
        "mapping_version": "m1",
        "record_type": "spatial_layer",
        "source_file_ref": "raw/flood.shp",
        "source_content_sha256": "c" * 64,
        "source_section": "flood",
        "source_feature_id": "12",
        "staged_at_utc": "2026-10-29T00:00:00Z",
    })
    return env


def run(attrs=None, **kw):
    args = dict(envelope=make_env(), layer_id="flood_2022", representation="vector",
                geometry_ref="raw/flood.shp#12", source_crs="EPSG:5186", bbox=(1, 2, 3, 4))
    args.update(kw)
    return normalize_feature({} if attrs is None else attrs, **args)


class TestVerdictFields(unittest.TestCase):
    def test_constant(self):
        self.assertEqual(VERDICT_FIELDS, ("verdict", "flooded", "inundated", "affected",
                                          "in_zone", "hazard_level", "risk_level"))


class TestNormalizeFeature(unittest.TestCase):
    def test_vector_accepted(self):
        out = run({"name": "zone A", "return_period_raw": "100"},
                  scenario="historic", event_date="2022-08-08")
        self.assertIsInstance(out, Outcome)
        self.assertEqual(out.status, "accepted")
        self.assertIsNone(out.reason)
        rec = out.record
        self.assertEqual(rec["layer_id"], "flood_2022")
        self.assertEqual(rec["representation"], "vector")
        self.assertEqual(rec["geometry_ref"], "raw/flood.shp#12")
        self.assertEqual(rec["source_crs"], "EPSG:5186")
        self.assertEqual(rec["bbox"], [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(rec["scenario"], "historic")
        self.assertEqual(rec["event_date"], "2022-08-08")
        self.assertEqual(rec["name"], "zone A")
        self.assertEqual(rec["return_period_raw"], "100")
        self.assertEqual(rec["source_id"], "safemap_flood")
        self.assertEqual(rec["validation_status"], "accepted")
        self.assertIsNone(rec["validation_reason"])

    def test_defaults_none(self):
        out = run(bbox=None)
        self.assertEqual(out.status, "accepted")
        self.assertIsNone(out.record["bbox"])
        self.assertIsNone(out.record["scenario"])
        self.assertIsNone(out.record["event_date"])

    def test_unknown_crs(self):
        out = run(source_crs=None)
        self.assertEqual(out.record["source_crs"], "unknown")
        self.assertEqual(out.status, "accepted")

    def test_image_drops_verdict(self):
        out = run({"flooded": "Y", "label": "tile"}, representation="image",
                  geometry_ref="raw/tile.png", bbox=None)
        self.assertEqual(out.status, "accepted")
        self.assertNotIn("flooded", out.record)
        self.assertEqual(out.record["label"], "tile")

    def test_missing_geometry_ref(self):
        out = run(geometry_ref=None)
        self.assertEqual(out.status, "rejected")
        self.assertEqual(out.reason, "missing_required:geometry_ref")
        self.assertEqual(out.record["validation_reason"], "missing_required:geometry_ref")

    def test_invalid_bbox(self):
        out = run(bbox=(3, 0, 1, 1))
        self.assertEqual(out.reason, "invalid_geometry:bbox")
        self.assertIsNone(out.record["bbox"])

    def test_invalid_event_date(self):
        out = run(event_date="2022-02-30")
        self.assertEqual(out.reason, "invalid_date:event_date")
        self.assertIsNone(out.record["event_date"])
        self.assertEqual(out.record["event_date_raw"], "2022-02-30")

    def test_invalid_representation(self):
        with self.assertRaises(C.ContractError) as ctx:
            run(representation="polygon")
        self.assertEqual(str(ctx.exception), "invalid_representation")


if __name__ == "__main__":
    unittest.main()

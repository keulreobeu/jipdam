import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.package.manifest_doc import (
    COUNT_KEYS, MANIFEST_KEYS, build_manifest, missing_keys, secret_shapes)

SHA = "a" * 64


def plan():
    return {"source_id": "seoul_subway", "dataset_id": "OA-1", "record_type": "facility",
            "batch_id": "seoul-subway-20261029-v1", "approval_ref": "approved",
            "record_url": "https://github.com/o/r/issues/7", "t_id": "T004"}


def dataset():
    return {"name": "Stations", "provider": "Seoul", "source": "https://data.seoul.go.kr/x",
            "mapping_version": "m1", "collection_method": "api", "scope": "Seoul",
            "request": {"region": "Seoul"}}


def build(**kw):
    args = dict(requests=[{"request_id": "r1", "collection_status": "complete"}],
                files=[{"path": "raw/a.json", "bytes": 3, "sha256": SHA}],
                counts={"expected_rows": 2, "raw_rows": 2, "accepted": 1, "excluded": 0, "rejected": 1},
                owner="cannedJean", dataset=dataset(), license={"raw": "KOGL type 1"},
                staged_at_utc="2026-10-29T00:00:00Z")
    args.update(kw)
    return build_manifest(plan(), **args)


class ManifestBuildTest(unittest.TestCase):
    def test_keys_and_values(self):
        m = build()
        self.assertEqual(list(m), list(MANIFEST_KEYS))
        self.assertEqual(len(MANIFEST_KEYS), 31)
        self.assertEqual(m["delivery_schema_version"], C.DELIVERY_SCHEMA_VERSION)
        self.assertEqual(m["quality_status"], C.QUALITY_STATUS)
        self.assertEqual(m["source_id"], "seoul_subway")
        self.assertEqual(m["dataset_id"], "OA-1")
        self.assertEqual(m["metadata_dataset_id"], "T004")
        self.assertEqual(m["dataset"], "Stations")
        self.assertEqual(m["kind"], "facility")
        self.assertEqual(m["owner"], "cannedJean")
        self.assertEqual(m["license_raw"], "KOGL type 1")
        self.assertIsNone(m["license_ref"])
        self.assertEqual(m["license_review_status"], "pending")
        self.assertEqual(m["collection_status"], "complete")
        self.assertIs(m["normalized_withheld"], False)
        self.assertEqual(m["files"], [{"path": "raw/a.json", "bytes": 3, "sha256": SHA}])
        self.assertEqual(list(m["counts"]), list(COUNT_KEYS))
        self.assertEqual(m["counts"]["rejected"], 1)
        self.assertEqual(m["staged_at_utc"], "2026-10-29T00:00:00Z")
        self.assertNotIn("container", m)

    def test_partial_status(self):
        m = build(requests=[{"collection_status": "complete"}, {"collection_status": "failed"}])
        self.assertEqual(m["collection_status"], "partial")

    def test_error_code(self):
        with self.assertRaises(C.ContractError) as ctx:
            build(requests=[])
        self.assertEqual(str(ctx.exception), "no_requests")


class ManifestMissingKeysTest(unittest.TestCase):
    def test_complete_and_missing(self):
        m = build()
        self.assertEqual(missing_keys(m), [])
        del m["owner"]
        del m["counts"]["rejected"]
        self.assertEqual(missing_keys(m), ["owner", "counts.rejected"])


class ManifestSecretShapesTest(unittest.TestCase):
    def test_paths(self):
        obj = {"a": ["x", "u?ServiceKey=abc"], "b": 1,
               "c": {"u": "http://h:8088/" + "A" * 20 + "/json/x/1/5/"}}
        self.assertEqual(secret_shapes(obj), ["$.a[1]", "$.c.u"])

    def test_clean(self):
        self.assertEqual(secret_shapes({"u": "http://h:8088/sample/xml/x/1/5/"}), [])


if __name__ == "__main__":
    unittest.main()

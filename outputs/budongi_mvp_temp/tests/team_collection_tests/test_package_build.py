"""Packaging shell: tree assembly, gates, license withholding and secret sweep (fake units)."""
from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from budongi.team_collection import contract as C
from budongi.team_collection.package_build import PackageUnits, build_package, collect_raw

KEY = "SeCrEtKeY123+=="
STAMP = (2026, 10, 30, 0, 0, 0)


def fake_units(record_errors=None, shapes=None, reconcile_errors=None):
    def write_zip(src, dest, *, arc_root, stamp):
        with zipfile.ZipFile(dest, "w") as zf:
            for path in sorted(p for p in Path(src).rglob("*") if p.is_file()):
                zf.writestr(f"{arc_root}/{path.relative_to(src)}".replace("\\", "/"),
                            path.read_bytes())
        return {"entries": len(zf.namelist()), "arc_root": arc_root, "stamp": list(stamp)}

    return PackageUnits(
        build_schema=lambda **kw: {"schema": "s", "source_id": kw["source_id"]},
        build_manifest=lambda plan, **kw: {"source_id": plan["source_id"],
                                           "batch_id": plan["batch_id"],
                                           "files": kw["files"], "counts": kw["counts"],
                                           "requests": kw["requests"],
                                           "normalized_withheld": kw["normalized_withheld"]},
        secret_shapes=lambda obj: list(shapes or []),
        reconcile=lambda stats: list(reconcile_errors or []),
        build_validation=lambda stats: {"reconciliation": "ok", "lane": stats["lane"]},
        check_records=lambda lines, *, manifest, files: {
            "ok": not record_errors, "errors": list(record_errors or []),
            "counts": {"lines": sum(1 for _ in lines)}},
        write_zip=write_zip,
        split_parts=lambda path, *, part_bytes: {"schema_version": "jipdam_zip_parts_v1",
                                                 "parts": 2})


def make_batch(root, license_class="kogl1"):
    batch = root / "batch"
    raw = batch / "raw" / "r1"
    raw.mkdir(parents=True)
    (raw / "p000001_a000001.csv").write_bytes(b"name,region\r\nx,seoul\r\n")
    (raw / "journal.json").write_text(json.dumps(
        {"status": "complete", "error": None,
         "pages": [{"file": "p000001_a000001.csv", "rows": 1}]}), encoding="utf-8")
    plan = {"source_id": "kric_station", "batch_id": "kric-station-20261030-v1", "lane": "A1",
            "record_type": "facility", "license": {"class": license_class, "ref": "url"},
            "requests": [{"request_id": "r1", "section": "s1", "expected_rows": 1,
                          "expected_basis": "provider"},
                         {"request_id": "r2", "section": "s1"}]}
    (batch / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    (batch / "normalized").mkdir()
    (batch / "normalized" / "facility.jsonl").write_text('{"a":1}\n{"a":2}\n', encoding="utf-8")
    (batch / "validation").mkdir()
    (batch / "validation" / "excluded.csv.gz").write_bytes(b"gz-bytes")
    staging = {"sections": [{"section": "s1", "raw": 3, "accepted": 2, "excluded": 1,
                             "rejected": 0}], "staged_at_utc": "2026-10-30T01:00:00Z"}
    return batch, plan, staging


def run_build(root, batch, plan, staging, units, keys=(KEY,), readme="# 재현\n"):
    dataset = {"mapping_version": "m1", "expected_rows": 1,
               "zip_name": "kric_station_facility_seoul_202610_20261030_kric-station-20261030-v1.zip"}
    return build_package(batch, root / "out", plan=plan, staging=staging,
                         schema_inputs={"source_id": plan["source_id"]}, dataset=dataset,
                         units=units, keys=list(keys), readme=readme,
                         extra_files={"code/REFERENCE.json": b"{}"}, stamp=STAMP)


class PackageBuildTests(unittest.TestCase):
    def test_tree_zip_counts_and_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch, plan, staging = make_batch(root)
            report = run_build(root, batch, plan, staging, fake_units())
            self.assertEqual(report["counts"], {"raw_rows": 3, "accepted": 2, "excluded": 1,
                                                "rejected": 0, "expected_rows": 1})
            self.assertEqual([r["collection_status"] for r in report["requests"]],
                             ["complete", "not_collected"])
            self.assertEqual(report["requests"][0]["received_rows"], 1)
            self.assertIsNone(report["parts"])
            with zipfile.ZipFile(report["zip"]) as zf:
                names = set(zf.namelist())
            root_prefix = "kric_station/kric-station-20261030-v1/"
            for expected in ("manifest.json", "schema.json", "validation.json", "README.md",
                             "normalized/facility.jsonl", "validation/excluded.csv.gz",
                             "raw/r1/p000001_a000001.csv", "collection/plan.json",
                             "collection/requests/r1.json", "code/REFERENCE.json"):
                self.assertIn(root_prefix + expected, names, expected)
            manifest = json.loads(Path(root / "out/tree/kric_station/kric-station-20261030-v1/"
                                       "manifest.json").read_text("utf-8"))
            listed = {f["path"]: f for f in manifest["files"]}
            self.assertNotIn("manifest.json", listed)
            normalized = listed["normalized/facility.jsonl"]
            self.assertEqual((normalized["format"], normalized["rows"]), ("jsonl", 2))
            self.assertFalse(manifest["normalized_withheld"])

    def test_restricted_license_withholds_normalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch, plan, staging = make_batch(root, license_class="kogl4")
            report = run_build(root, batch, plan, staging, fake_units())
            self.assertTrue(report["normalized_withheld"])
            with zipfile.ZipFile(report["zip"]) as zf:
                self.assertFalse([n for n in zf.namelist() if "normalized/" in n])

    def test_gates_refuse_bad_outputs(self):
        cases = [(fake_units(reconcile_errors=["raw_mismatch:s1"]), "reconcile_failed:raw_mismatch:s1"),
                 (fake_units(record_errors=["invalid_sha:1"]), "record_check_failed:invalid_sha:1"),
                 (fake_units(shapes=["manifest.requests.0.url"]), "manifest_secret_shape")]
        for units, code in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                batch, plan, staging = make_batch(root)
                with self.assertRaises(C.ContractError, msg=code) as cm:
                    run_build(root, batch, plan, staging, units)
                self.assertEqual(str(cm.exception), code)

    def test_secret_sweep_blocks_leaky_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch, plan, staging = make_batch(root)
            with self.assertRaises(C.ContractError) as cm:
                run_build(root, batch, plan, staging, fake_units(),
                          readme=f"# 재현\nkey={KEY}\n")
            self.assertEqual(str(cm.exception), "secret_in_package_tree")

    def test_split_when_over_part_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch, plan, staging = make_batch(root)
            dataset = {"mapping_version": "m1", "expected_rows": None, "zip_name": "x.zip"}
            report = build_package(batch, root / "out", plan=plan, staging=staging,
                                   schema_inputs={"source_id": plan["source_id"]},
                                   dataset=dataset, units=fake_units(), keys=[KEY],
                                   readme="# r\n", stamp=STAMP, part_bytes=10)
            self.assertEqual(report["parts"]["schema_version"], "jipdam_zip_parts_v1")

    def test_collect_raw_orders_by_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, _ = make_batch(Path(tmp))
            copies, requests = collect_raw(batch, plan)
            self.assertEqual([r["request_id"] for r in requests], ["r1", "r2"])
            self.assertEqual([rel for _, rel, _extra in copies],
                             ["collection/requests/r1.json", "raw/r1/p000001_a000001.csv"])
            self.assertEqual(copies[1][2],
                             {"format": "csv", "section": "s1", "rows": 1, "encoding": None})


if __name__ == "__main__":
    unittest.main()

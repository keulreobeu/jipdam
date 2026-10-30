"""Staging shell: counts, excluded bucket, idempotence and determinism (fake units, no I/O deps)."""
from __future__ import annotations

import csv
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from budongi.team_collection import contract as C
from budongi.team_collection.base import Outcome, RawRow
from budongi.team_collection.stage import StageFile, StageUnits, stage_batch

CTX = SimpleNamespace(batch_id="src-20261030-v1", staged_at_utc="2026-10-30T01:00:00Z")


def fake_units():
    def apply_mapping(mapping, header, values):
        if values[0] == "bad":
            return {"name": None, "name_raw": "bad"}, ["invalid_number:name"]
        return {"name": values[0], "region": values[1]}, []

    def make_envelope(ctx, *, file_ref, file_sha, section, position=None, feature_id=None):
        return {"batch_id": ctx.batch_id, "source_file_ref": file_ref, "source_section": section,
                "source_row_number": position, "source_feature_id": feature_id}

    def normalize(fields, envelope):
        record = {**envelope, "name": fields["name"], "validation_status": "accepted",
                  "validation_reason": None}
        if fields["name"] == "twice":
            return [Outcome(record, "accepted"), Outcome({**record, "name": "twice-2"}, "accepted")]
        return Outcome(record, "accepted")

    return StageUnits(
        compile_mapping=lambda doc: dict(doc),
        apply_mapping=apply_mapping,
        header_coverage=lambda mapping, header: {"complete": header == ("name", "region")},
        make_envelope=make_envelope,
        finalize=lambda record, status, reason: {**record, "validation_status": status,
                                                 "validation_reason": reason},
        normalize=normalize)


def scope(fields):
    return {"seoul": "in", "busan": "out"}.get(fields.get("region"), "unknown")


ROWS = [RawRow("s1", 1, ("가나", "seoul")),
        RawRow("s1", 2, (), status="blank", reason="blank_row"),
        RawRow("s1", 3, ("x", "seoul", "extra"), status="ragged", reason="ragged_row"),
        RawRow("s1", 4, ("bad", "seoul")),
        RawRow("s1", 5, ("바다", "busan")),
        RawRow("s1", 6, ("몰라", "")),
        RawRow("s1", 7, ("twice", "seoul"))]


def one_file(rows=None):
    return [StageFile(file_ref="raw/r1/p000001_a000001.csv", sha256="a" * 64, section="s1",
                      read=lambda: (("name", "region"), iter(rows or ROWS)))]


def run(folder, files=None, code="c1"):
    return stage_batch(folder, ctx=CTX, record_type="facility", mapping_doc={"v": 1},
                       files=files or one_file(), units=fake_units(), scope=scope,
                       code_signature=code)


class StageTests(unittest.TestCase):
    def test_counts_jsonl_and_excluded_bucket(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = run(Path(tmp))
            self.assertEqual(summary["sections"],
                             [{"section": "s1", "raw": 7, "accepted": 3, "excluded": 3,
                               "rejected": 2}])
            self.assertEqual((summary["jsonl_lines"], summary["new_rows"]), (5, 5))
            lines = [json.loads(l) for l in
                     (Path(tmp) / "normalized/facility.jsonl").read_text("utf-8").splitlines()]
            self.assertEqual([l["validation_status"] for l in lines],
                             ["accepted", "rejected", "rejected", "accepted", "accepted"])
            self.assertEqual(lines[1]["source_cells_json"], '["x", "seoul", "extra"]')
            self.assertEqual(lines[2]["validation_reason"], "invalid_number:name")
            self.assertEqual(lines[2]["name_raw"], "bad")
            with gzip.open(Path(tmp) / "validation/excluded.csv.gz", "rt", encoding="utf-8") as fh:
                rows = list(csv.reader(fh))
            self.assertEqual(rows[0], ["file_ref", "section", "position", "reason", "values_json"])
            self.assertEqual([(r[2], r[3]) for r in rows[1:]],
                             [("2", "blank_row"), ("5", "out_of_scope_region"),
                              ("6", "scope_undetermined")])

    def test_rerun_is_idempotent_and_change_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            run(Path(tmp))
            before = (Path(tmp) / "normalized/facility.jsonl").read_bytes()
            again = run(Path(tmp))
            self.assertTrue(again["resumed"])
            self.assertEqual(again["new_rows"], 0)
            self.assertEqual((Path(tmp) / "normalized/facility.jsonl").read_bytes(), before)
            with self.assertRaisesRegex(C.ContractError, "input_changed_use_new_batch"):
                run(Path(tmp), code="c2")

    def test_two_fresh_runs_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            run(Path(a))
            run(Path(b))
            for name in ("normalized/facility.jsonl", "validation/excluded.csv.gz"):
                self.assertEqual((Path(a) / name).read_bytes(), (Path(b) / name).read_bytes(), name)

    def test_incomplete_mapping_and_bad_record_type_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = [StageFile(file_ref="raw/r1/x.csv", sha256="b" * 64, section="s9",
                               read=lambda: (("other",), iter([])))]
            with self.assertRaisesRegex(C.ContractError, "mapping_incomplete:s9"):
                run(Path(tmp), files=files)
            self.assertFalse((Path(tmp) / "staging.json").exists())
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(C.ContractError, "invalid_record_type"):
                stage_batch(Path(tmp), ctx=CTX, record_type="raw_only", mapping_doc={},
                            files=one_file(), units=fake_units(), scope=scope, code_signature="c")

    def test_feature_position_kind_uses_feature_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = [StageFile(file_ref="raw/r1/x.shp", sha256="c" * 64, section="s1",
                               read=lambda: (("name", "region"),
                                             iter([RawRow("s1", 11, ("강", "seoul"))])),
                               position_kind="feature")]
            run(Path(tmp), files=files)
            line = json.loads((Path(tmp) / "normalized/facility.jsonl").read_text("utf-8"))
            self.assertEqual((line["source_feature_id"], line["source_row_number"]), ("11", None))


if __name__ == "__main__":
    unittest.main()

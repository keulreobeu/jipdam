"""Profiling shell: accumulator wiring, bounded distinct, rule flags (fake units)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from budongi.team_collection import contract as C
from budongi.team_collection.profile_run import (ProfileUnits, coord_ok, digest_set, jsonl_rows,
                                                 kind_set, profile_batch)


class FakeColumn:
    def __init__(self, name, *, kind, classify, rule, distinct):
        self.name, self.kind, self.classify, self.rule, self.distinct = \
            name, kind, classify, rule, distinct
        self.values, self.firsts = [], []

    def add(self, value):
        self.values.append(value)
        if isinstance(value, str):
            self.firsts.append(self.distinct(value))

    def result(self):
        return {"name": self.name, "kind": self.kind, "total": len(self.values),
                "firsts": list(self.firsts)}


class FakeRows:
    def __init__(self, **kwargs):
        self.kwargs, self.rows = kwargs, []

    def add(self, row, *, rule_failed=False):
        self.rows.append((row.get("name"), rule_failed))

    def result(self):
        return {"total": len(self.rows), "flags": [f for _, f in self.rows]}


class Capture:
    def __init__(self):
        self.columns, self.rows_kwargs, self.rules = [], None, []

    def units(self):
        def column(name, **kwargs):
            acc = FakeColumn(name, **kwargs)
            self.columns.append(acc)
            return acc

        def rows(**kwargs):
            self.rows_kwargs = kwargs
            return FakeRows(**kwargs)

        def compile_rule(text):
            self.rules.append(text)
            return lambda value: value != "이상"

        return ProfileUnits(column_accumulator=column, row_accumulator=rows,
                            compile_rule=compile_rule,
                            classify_value=lambda v, *, kind, extra:
                            "null" if v is None else "semantic" if v in extra else "present")


RECORDS = [{"name": "강남", "code": "01"}, {"name": "강남", "code": "01"},
            {"name": "이상", "code": "02"}, {"name": None, "code": "-"}]


class ProfileBatchTests(unittest.TestCase):
    def test_wiring_order_distinct_and_rule_flags(self):
        cap = Capture()
        report = profile_batch(iter(RECORDS), units=cap.units(),
                               columns=[{"name": "name", "kind": "text", "rule": "no-이상"},
                                        {"name": "code", "kind": "code", "extra": ["-"]}],
                               pk=("code",))
        self.assertEqual([c["name"] for c in report["columns"]], ["name", "code"])
        self.assertEqual(report["total"], 4)
        self.assertEqual(cap.rules, ["no-이상"])        # compiled once
        name_acc = cap.columns[0]
        self.assertEqual(name_acc.values, ["강남", "강남", "이상", None])
        self.assertEqual(name_acc.firsts, [True, False, True])   # digest-bounded distinct
        self.assertIsNone(cap.columns[1].rule)
        self.assertEqual(cap.columns[1].classify("-"), "semantic")
        self.assertEqual(cap.columns[1].classify(None), "null")
        self.assertEqual(report["rows"]["flags"], [False, False, True, False])
        self.assertEqual(cap.rows_kwargs["pk"], ("code",))
        self.assertIs(cap.rows_kwargs["coord_ok"], coord_ok)

    def test_empty_columns_refused(self):
        with self.assertRaisesRegex(C.ContractError, "profile_without_columns"):
            profile_batch(iter([]), units=Capture().units(), columns=[])


class HelperTests(unittest.TestCase):
    def test_digest_and_kind_sets(self):
        first = digest_set()
        self.assertEqual([first("a"), first("a"), first("b")], [True, False, True])
        seen = kind_set()
        self.assertTrue(seen("row", "d1"))
        self.assertFalse(seen("row", "d1"))
        self.assertTrue(seen("pk", "d1"))     # kinds are independent

    def test_coord_ok_bounds(self):
        self.assertTrue(coord_ok("127.0", "37.5"))
        self.assertFalse(coord_ok("37.5", "127.0"))   # swapped axes fall outside
        self.assertFalse(coord_ok("x", "37.5"))
        self.assertFalse(coord_ok(None, "37.5"))

    def test_jsonl_rows_streams_and_rejects_non_dicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "facility.jsonl"
            path.write_text('{"a": 1}\n\n{"b": "강남"}\n', encoding="utf-8")
            self.assertEqual(list(jsonl_rows(path)), [{"a": 1}, {"b": "강남"}])
            path.write_text('[1]\n', encoding="utf-8")
            with self.assertRaisesRegex(C.ContractError, "invalid_jsonl_record"):
                list(jsonl_rows(path))


if __name__ == "__main__":
    unittest.main()

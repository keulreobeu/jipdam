"""Visible tests for H6 profile/metrics.py (typical paths)."""
from __future__ import annotations

import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.profile.metrics import ColumnAccumulator

KEYS = ["name", "total", "null", "semantic", "missing", "distinct", "examples",
        "min", "max", "mean", "median", "checked", "failures"]


def classify(value):
    if value is None:
        return "null"
    if isinstance(value, str) and value.strip() in ("", "-"):
        return "semantic"
    return "present"


def seen_set():
    seen = set()

    def distinct(text):
        if text in seen:
            return False
        seen.add(text)
        return True
    return distinct


def make(kind, rule=None, name="col"):
    return ColumnAccumulator(name, kind=kind, classify=classify, rule=rule,
                             distinct=seen_set())


class H6VisibleAccumulatorTest(unittest.TestCase):
    def test_numeric_typical_path(self):
        acc = make("numeric")
        for v in ["3", "1", None, "-", "2", "4", "2"]:
            acc.add(v)
        r = acc.result()
        self.assertEqual(list(r), KEYS)
        self.assertEqual(r["name"], "col")
        self.assertEqual((r["total"], r["null"], r["semantic"], r["missing"]),
                         (7, 1, 1, 2))
        self.assertEqual(r["distinct"], 4)
        self.assertEqual(r["examples"], ["3", "1", "2"])
        self.assertEqual((r["min"], r["max"]), ("1", "4"))
        self.assertEqual(r["mean"], 2.4)
        self.assertEqual(r["median"], 2.0)
        self.assertEqual((r["checked"], r["failures"]), (0, 0))

    def test_numeric_rule_and_unparsable(self):
        acc = make("numeric", rule=lambda t: not t.startswith("-"))
        for v in ["5", "-1", "abc"]:
            acc.add(v)
        r = acc.result()
        self.assertEqual((r["checked"], r["failures"]), (3, 2))
        self.assertEqual((r["min"], r["max"]), ("-1", "5"))
        self.assertEqual((r["mean"], r["median"]), (2.0, 2.0))
        self.assertEqual(r["distinct"], 3)

    def test_coordinate_even_median(self):
        acc = make("coordinate")
        acc.add("126.9")
        acc.add("127.1")
        r = acc.result()
        self.assertEqual((r["min"], r["max"]), ("126.9", "127.1"))
        self.assertEqual(r["median"], 127.0)
        self.assertEqual(r["mean"], 127.0)

    def test_text_with_rule(self):
        acc = make("text", rule=lambda t: t.startswith("A"))
        for v in ["A1", "bb", "A2", None]:
            acc.add(v)
        r = acc.result()
        self.assertEqual((r["total"], r["null"], r["missing"]), (4, 1, 1))
        self.assertEqual((r["checked"], r["failures"]), (3, 1))
        self.assertEqual(r["examples"], ["A1", "bb", "A2"])
        self.assertEqual((r["min"], r["max"], r["mean"], r["median"]),
                         (None, None, None, None))

    def test_date_min_max(self):
        acc = make("date")
        for v in ["2024-03-01", "2023-12-31", "2024-01-15"]:
            acc.add(v)
        r = acc.result()
        self.assertEqual((r["min"], r["max"]), ("2023-12-31", "2024-03-01"))
        self.assertIsNone(r["mean"])
        self.assertIsNone(r["median"])
        self.assertEqual(r["distinct"], 3)

    def test_invalid_kind(self):
        with self.assertRaises(C.ContractError) as cm:
            make("float")
        self.assertEqual(str(cm.exception), "invalid_kind")


if __name__ == "__main__":
    unittest.main()

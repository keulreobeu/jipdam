import unittest

from budongi.team_collection.profile.keys import RowAccumulator

KEYS = {"total", "full_duplicates", "pk_duplicates", "pk_missing", "address_present",
        "coord_present", "coord_valid", "rule_failed_rows"}


class SetSeen:
    def __init__(self):
        self.store = set()
        self.calls = []

    def __call__(self, kind, digest):
        self.calls.append((kind, digest))
        key = (kind, digest)
        if key in self.store:
            return False
        self.store.add(key)
        return True


def _missing(value):
    return value is None or (isinstance(value, str) and value.strip() == "")


def _seoul(x, y):
    return 126.0 <= float(x) <= 128.0 and 37.0 <= float(y) <= 38.0


def _make(seen=None, pk=("id",)):
    return RowAccumulator(pk=pk, address_cols=("road", "jibun"), coord_cols=("x", "y"),
                          coord_ok=_seoul, seen=seen if seen is not None else SetSeen(),
                          missing=_missing)


class TestRowAccumulatorVisible(unittest.TestCase):
    def test_typical_counts(self):
        acc = _make()
        r1 = {"id": "1", "road": "A", "jibun": None, "x": "127.0", "y": "37.5"}
        acc.add(r1)
        acc.add(dict(r1))
        acc.add({"id": "2", "road": "", "jibun": "B", "x": "200", "y": "37.5"})
        acc.add({"id": None, "road": None, "jibun": "", "x": "abc", "y": "1"}, rule_failed=True)
        acc.add({"id": "2", "road": "C", "jibun": None, "x": None, "y": None})
        self.assertEqual(acc.result(), {
            "total": 5, "full_duplicates": 1, "pk_duplicates": 2, "pk_missing": 1,
            "address_present": 4, "coord_present": 3, "coord_valid": 2, "rule_failed_rows": 1,
        })

    def test_empty_result_all_zero(self):
        res = _make().result()
        self.assertEqual(set(res), KEYS)
        self.assertTrue(all(v == 0 for v in res.values()))

    def test_seen_receives_row_then_pk_hex_digests(self):
        seen = SetSeen()
        acc = _make(seen)
        acc.add({"id": "7", "road": "A", "jibun": None, "x": "127", "y": "37"})
        self.assertEqual([k for k, _ in seen.calls], ["row", "pk"])
        for _, digest in seen.calls:
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertEqual(acc.result()["total"], 1)

    def test_composite_pk_duplicate_not_full_duplicate(self):
        acc = _make(pk=("id", "road"))
        acc.add({"id": "1", "road": "A", "jibun": "J1", "x": None, "y": None})
        acc.add({"id": "1", "road": "A", "jibun": "J2", "x": None, "y": None})
        res = acc.result()
        self.assertEqual(res["full_duplicates"], 0)
        self.assertEqual(res["pk_duplicates"], 1)
        self.assertEqual(res["pk_missing"], 0)

    def test_rule_failed_counted(self):
        acc = _make()
        acc.add({"id": "1"}, rule_failed=True)
        acc.add({"id": "2"}, rule_failed=False)
        acc.add({"id": "3"})
        res = acc.result()
        self.assertEqual(res["rule_failed_rows"], 1)
        self.assertEqual(res["total"], 3)


if __name__ == "__main__":
    unittest.main()

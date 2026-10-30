import unittest

from budongi.team_collection.xcheck.recount import recount_rows

MARKERS = {"-", "미상"}


def run(rows, *, columns=(), pk=(), address_cols=(), coord_cols=None, markers=MARKERS):
    return recount_rows(rows, columns=list(columns), pk=list(pk), address_cols=list(address_cols),
                        coord_cols=coord_cols, markers=markers)


class TestX2Columns(unittest.TestCase):
    def test_column_counts(self):
        rows = [{"a": "x", "b": "1"}, {"a": "-", "b": "1"}, {"a": None, "b": "2"},
                {"a": "y", "b": " 미상 "}]
        res = run(rows, columns=["a", "b"])
        self.assertEqual(res["total"], 4)
        self.assertEqual(list(res["columns"]), ["a", "b"])
        self.assertEqual(res["columns"]["a"], {"total": 4, "null": 1, "semantic": 1, "missing": 2,
                                               "present": 2, "distinct": 2})
        self.assertEqual(res["columns"]["b"], {"total": 4, "null": 0, "semantic": 1, "missing": 1,
                                               "present": 3, "distinct": 2})

    def test_result_keys(self):
        res = run([{"a": "x"}], columns=["a"])
        self.assertEqual(set(res), {"total", "columns", "full_duplicates", "pk_duplicates",
                                    "pk_missing", "address_present", "coord_present",
                                    "coord_valid"})


class TestX2Rows(unittest.TestCase):
    def test_full_and_pk_duplicates(self):
        rows = [{"id": "1", "v": "a"}, {"id": "1", "v": "a"}, {"id": "1", "v": "b"},
                {"id": "2", "v": "a"}, {"id": "-", "v": "a"}, {"id": None, "v": "c"}]
        res = run(rows, pk=["id"])
        self.assertEqual(res["full_duplicates"], 1)
        self.assertEqual(res["pk_duplicates"], 2)
        self.assertEqual(res["pk_missing"], 2)

    def test_composite_pk(self):
        rows = [{"a": "1", "b": "x"}, {"a": "1", "b": "y"}, {"a": "1", "b": "x", "c": "z"}]
        res = run(rows, pk=["a", "b"])
        self.assertEqual(res["pk_duplicates"], 1)
        self.assertEqual(res["full_duplicates"], 0)
        self.assertEqual(res["pk_missing"], 0)

    def test_address_present(self):
        rows = [{"road": "세종대로 110", "jibun": None}, {"road": "-", "jibun": "태평로1가 31"},
                {"road": None, "jibun": "미상"}]
        res = run(rows, address_cols=["road", "jibun"])
        self.assertEqual(res["address_present"], 2)

    def test_coordinates(self):
        rows = [{"x": "126.978", "y": "37.566"}, {"x": "37.566", "y": "126.978"},
                {"x": "abc", "y": "37.5"}, {"x": None, "y": "37.5"}, {"x": 127, "y": 37.5}]
        res = run(rows, coord_cols=("x", "y"))
        self.assertEqual(res["coord_present"], 3)
        self.assertEqual(res["coord_valid"], 2)

    def test_empty_rows(self):
        res = run([], columns=["a"], pk=["a"], address_cols=["a"], coord_cols=("x", "y"))
        self.assertEqual(res["total"], 0)
        self.assertEqual(res["columns"]["a"]["present"], 0)
        for key in ("full_duplicates", "pk_duplicates", "pk_missing", "address_present",
                    "coord_present", "coord_valid"):
            self.assertEqual(res[key], 0, key)


if __name__ == "__main__":
    unittest.main()

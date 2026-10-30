import unittest
from datetime import date

from budongi.team_collection import contract as C
from budongi.team_collection.core.ids import (
    check_ids,
    issue_id,
    make_batch_id,
    next_dataset_id,
    zip_name,
)


class TestC1MakeBatchId(unittest.TestCase):
    def test_date_collected_no_period(self):
        self.assertEqual(make_batch_id("seoul-bus-stops", collected=date(2026, 10, 29)),
                         "seoul-bus-stops-20261029-v1")

    def test_normalised_slug_period_version(self):
        out = make_batch_id(" Seoul_Bus ", period="202401-202608", collected="20261029", version=2)
        self.assertEqual(out, "seoul-bus-202401-202608-20261029-v2")
        self.assertIsNotNone(C.BATCH_ID_RE.fullmatch(out))

    def test_period_lowercased(self):
        self.assertEqual(make_batch_id("seoul", period="2024Q1", collected="20261029"),
                         "seoul-2024q1-20261029-v1")

    def test_invalid_slug(self):
        with self.assertRaises(C.ContractError) as cm:
            make_batch_id("a--b", collected="20261029")
        self.assertEqual(str(cm.exception), "invalid_slug")

    def test_too_long(self):
        with self.assertRaises(C.ContractError) as cm:
            make_batch_id("a" * 69, collected="20261029")
        self.assertEqual(str(cm.exception), "batch_id_too_long")


class TestC1ZipName(unittest.TestCase):
    def test_typical(self):
        out = zip_name(provider="seoul", kind="busstop", region="seoul", period="202610",
                       collected="20261029", batch_id="seoul-bus-20261029-v1")
        self.assertEqual(out, "seoul_busstop_seoul_202610_20261029_seoul-bus-20261029-v1.zip")

    def test_date_collected(self):
        out = zip_name(provider="p", kind="k", region="r", period="x",
                       collected=date(2026, 1, 5), batch_id="s-20260105-v1")
        self.assertEqual(out, "p_k_r_x_20260105_s-20260105-v1.zip")

    def test_underscore_part_rejected(self):
        with self.assertRaises(C.ContractError) as cm:
            zip_name(provider="a_b", kind="k", region="r", period="p",
                     collected="20261029", batch_id="s-20261029-v1")
        self.assertEqual(str(cm.exception), "invalid_zip_part")


class TestC1CheckIds(unittest.TestCase):
    def test_valid_returns_none(self):
        self.assertIsNone(check_ids(source_id="seoul_bus", batch_id="seoul-bus-20261029-v1",
                                    t_id="T001"))
        with self.assertRaises(C.ContractError) as cm:
            check_ids(source_id="seoul_bus", batch_id="seoul-bus-20261029-v1", t_id="T0001")
        self.assertEqual(str(cm.exception), "invalid_t_id")

    def test_invalid_source_id(self):
        with self.assertRaises(C.ContractError) as cm:
            check_ids(source_id="Seoul", batch_id="seoul-bus-20261029-v1", t_id="T001")
        self.assertEqual(str(cm.exception), "invalid_source_id")


class TestC1NextDatasetId(unittest.TestCase):
    def test_next_after_max(self):
        self.assertEqual(next_dataset_id(["T001", "T003", "R009", "x"]), "T004")

    def test_empty(self):
        self.assertEqual(next_dataset_id([]), "T001")

    def test_other_prefix(self):
        self.assertEqual(next_dataset_id(["T001", "R009"], prefix="R"), "R010")

    def test_exhausted(self):
        with self.assertRaises(C.ContractError) as cm:
            next_dataset_id(["T999"])
        self.assertEqual(str(cm.exception), "dataset_id_exhausted")


class TestC1IssueId(unittest.TestCase):
    def test_issue_ids(self):
        self.assertEqual(issue_id(1), "T-I001")
        self.assertEqual(issue_id(42), "T-I042")

    def test_zero_rejected(self):
        with self.assertRaises(C.ContractError) as cm:
            issue_id(0)
        self.assertEqual(str(cm.exception), "invalid_issue_number")


if __name__ == "__main__":
    unittest.main()

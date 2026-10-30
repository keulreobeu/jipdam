from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from budongi.team_collection import contract as C
from budongi.team_collection.core.timefmt import (
    FREQUENCIES,
    iso_date,
    kst_to_utc_z,
    period_key,
    utc_z,
)

KST = timezone(timedelta(hours=9))


class C2UtcZTests(unittest.TestCase):
    def test_utc_value_formatted(self):
        value = datetime(2024, 3, 1, 12, 34, 56, tzinfo=timezone.utc)
        self.assertEqual(utc_z(value), "2024-03-01T12:34:56Z")

    def test_kst_value_converted(self):
        self.assertEqual(utc_z(datetime(2024, 3, 1, 9, 0, tzinfo=KST)), "2024-03-01T00:00:00Z")

    def test_naive_rejected(self):
        with self.assertRaises(C.ContractError) as cm:
            utc_z(datetime(2024, 3, 1))
        self.assertEqual(str(cm.exception), "naive_datetime")


class C2KstToUtcTests(unittest.TestCase):
    def test_minutes_format(self):
        self.assertEqual(kst_to_utc_z("2024-03-01 09:30", fmt="%Y-%m-%d %H:%M"),
                         "2024-03-01T00:30:00Z")

    def test_crosses_back_into_previous_day(self):
        self.assertEqual(kst_to_utc_z("20240301 0800", fmt="%Y%m%d %H%M"), "2024-02-29T23:00:00Z")

    def test_24_00_means_next_day(self):
        self.assertEqual(kst_to_utc_z("2024-01-31 24:00", fmt="%Y-%m-%d %H:%M"),
                         "2024-01-31T15:00:00Z")

    def test_unparsable_rejected(self):
        with self.assertRaises(C.ContractError) as cm:
            kst_to_utc_z("abc", fmt="%Y-%m-%d %H:%M")
        self.assertEqual(str(cm.exception), "invalid_datetime")


class C2IsoDateTests(unittest.TestCase):
    def test_all_four_forms(self):
        for text in ("20240229", "2024-02-29", "2024.02.29", "2024/02/29"):
            with self.subTest(text=text):
                self.assertEqual(iso_date(text), "2024-02-29")

    def test_none_and_empty(self):
        self.assertIsNone(iso_date(None))
        self.assertIsNone(iso_date(""))
        self.assertEqual(iso_date("20240101"), "2024-01-01")

    def test_calendar_checked(self):
        with self.assertRaises(C.ContractError) as cm:
            iso_date("2023-02-29")
        self.assertEqual(str(cm.exception), "invalid_date")


class C2PeriodKeyTests(unittest.TestCase):
    def test_frequencies_constant(self):
        self.assertEqual(FREQUENCIES, ("daily", "monthly", "quarterly", "yearly"))
        self.assertEqual(period_key("2024", frequency=FREQUENCIES[3]), "2024")

    def test_monthly(self):
        for text in ("202401", "2024-01", "2024.01", "2024/01"):
            with self.subTest(text=text):
                self.assertEqual(period_key(text, frequency="monthly"), "2024-01")

    def test_daily(self):
        self.assertEqual(period_key("20240105", frequency="daily"), "2024-01-05")

    def test_yearly(self):
        self.assertEqual(period_key("2024", frequency="yearly"), "2024")

    def test_quarterly_forms(self):
        cases = {"2024Q1": "2024-Q1", "2024-Q2": "2024-Q2", "2024 3분기": "2024-Q3"}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(period_key(text, frequency="quarterly"), expected)

    def test_unknown_frequency(self):
        with self.assertRaises(C.ContractError) as cm:
            period_key("2024", frequency="weekly")
        self.assertEqual(str(cm.exception), "invalid_frequency")


if __name__ == "__main__":
    unittest.main()

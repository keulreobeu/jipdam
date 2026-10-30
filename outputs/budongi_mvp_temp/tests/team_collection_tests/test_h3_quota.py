from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from budongi.team_collection.runtime.quota import QuotaLedger, kst_day

UTC = timezone.utc
KEY = "0123456789abcdef" * 4


class _Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class QuotaVisibleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._tmp.name) / "quota.sqlite3"
        self.clock = _Clock(datetime(2026, 10, 29, 3, 0, 0, tzinfo=UTC))
        self.ledger = QuotaLedger(self.path, clock=self.clock)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_kst_day_converts_to_utc_plus_9(self) -> None:
        self.assertEqual(kst_day(datetime(2026, 10, 29, 14, 59, 59, tzinfo=UTC)), "2026-10-29")
        self.assertEqual(kst_day(datetime(2026, 10, 29, 15, 0, 0, tzinfo=UTC)), "2026-10-30")

    def test_snapshot_of_absent_row_is_zero(self) -> None:
        self.assertEqual(
            self.ledger.snapshot(KEY, "seoul:daily"),
            {"kst_day": "2026-10-29", "cap": 0, "reserved": 0, "used": 0,
             "blocked_until_utc": None},
        )

    def test_reserve_within_limit_updates_snapshot(self) -> None:
        self.assertIs(self.ledger.reserve(KEY, "seoul:daily", 90, cap=100), True)
        self.assertEqual(
            self.ledger.snapshot(KEY, "seoul:daily"),
            {"kst_day": "2026-10-29", "cap": 100, "reserved": 90, "used": 0,
             "blocked_until_utc": None},
        )

    def test_reserve_refused_above_stop_ratio(self) -> None:
        self.assertIs(self.ledger.reserve(KEY, "b", 95, cap=100), True)
        self.assertIs(self.ledger.reserve(KEY, "b", 1, cap=100), False)
        self.assertEqual(self.ledger.snapshot(KEY, "b")["reserved"], 95)

    def test_commit_moves_reserved_to_used(self) -> None:
        self.ledger.reserve(KEY, "b", 10, cap=100)
        self.assertIsNone(self.ledger.commit(KEY, "b", used=7, reserved=10))
        snap = self.ledger.snapshot(KEY, "b")
        self.assertEqual((snap["reserved"], snap["used"]), (0, 7))

    def test_release_returns_reserved_units(self) -> None:
        self.ledger.reserve(KEY, "b", 10, cap=100)
        self.assertIsNone(self.ledger.release(KEY, "b", 4))
        self.assertEqual(self.ledger.snapshot(KEY, "b")["reserved"], 6)

    def test_block_until_reset_returns_next_kst_midnight(self) -> None:
        until = self.ledger.block_until_reset(KEY, "b")
        self.assertEqual(until, "2026-10-29T15:00:00Z")
        self.assertIs(self.ledger.reserve(KEY, "b", 1, cap=100), False)
        self.assertEqual(self.ledger.snapshot(KEY, "b")["blocked_until_utc"], until)


if __name__ == "__main__":
    unittest.main()

"""Daily API quota ledger backed by SQLite with KST day boundaries."""
from __future__ import annotations

import math
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from budongi.team_collection import contract as C

_KST = timezone(timedelta(hours=9))


def kst_day(moment: datetime) -> str:
    """Return the calendar date of an aware datetime in UTC+9 as 'YYYY-MM-DD'."""
    if not isinstance(moment, datetime):
        raise C.ContractError("naive_datetime")
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise C.ContractError("naive_datetime")
    return moment.astimezone(_KST).strftime("%Y-%m-%d")


def _validate_key_ref(key_ref: object) -> None:
    if not isinstance(key_ref, str) or not C.SHA256_RE.fullmatch(key_ref):
        raise C.ContractError("invalid_key_ref")


def _validate_bucket(bucket: object) -> None:
    if not isinstance(bucket, str) or not bucket:
        raise C.ContractError("invalid_bucket")


def _validate_amount_positive(n: object) -> None:
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise C.ContractError("invalid_amount")


def _validate_amount_non_negative(n: object) -> None:
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise C.ContractError("invalid_amount")


def _validate_cap(cap: object) -> None:
    if isinstance(cap, bool) or not isinstance(cap, int) or cap < 1:
        raise C.ContractError("invalid_cap")


class QuotaLedger:
    """SQLite-backed ledger of daily quota per (key_ref, bucket, KST day)."""

    def __init__(self, path: Path, *, clock: Callable[[], datetime]) -> None:
        """Create the database file and the quota table if absent."""
        self._path = Path(path)
        self._clock = clock
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._path), timeout=30.0, isolation_level=None)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS quota ("
                "key_ref TEXT, "
                "bucket TEXT, "
                "kst_day TEXT, "
                "cap INTEGER, "
                "reserved INTEGER, "
                "used INTEGER, "
                "blocked_until_utc TEXT, "
                "PRIMARY KEY (key_ref, bucket, kst_day)"
                ")"
            )
        finally:
            conn.close()

    def reserve(self, key_ref: str, bucket: str, n: int, *, cap: int) -> bool:
        """Reserve n units for today if not blocked and within quota limit."""
        _validate_key_ref(key_ref)
        _validate_bucket(bucket)
        _validate_amount_positive(n)
        _validate_cap(cap)

        now = self._clock()
        today = kst_day(now)
        limit = math.floor(cap * C.QUOTA_STOP_RATIO)

        conn = sqlite3.connect(str(self._path), timeout=30.0, isolation_level=None)
        in_tx = False
        try:
            conn.execute("BEGIN IMMEDIATE")
            in_tx = True
            cur = conn.cursor()
            cur.execute(
                "SELECT reserved, used, blocked_until_utc FROM quota "
                "WHERE key_ref = ? AND bucket = ? AND kst_day = ?",
                (key_ref, bucket, today),
            )
            row = cur.fetchone()
            if row is None:
                cur_reserved = 0
                cur_used = 0
                cur_blocked = None
                row_exists = False
            else:
                cur_reserved = int(row[0])
                cur_used = int(row[1])
                cur_blocked = row[2]
                row_exists = True

            if cur_blocked is not None:
                blocked_dt = datetime.strptime(cur_blocked, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if now < blocked_dt:
                    conn.execute("ROLLBACK")
                    in_tx = False
                    return False

            if cur_used + cur_reserved + n > limit:
                conn.execute("ROLLBACK")
                in_tx = False
                return False

            if row_exists:
                conn.execute(
                    "UPDATE quota SET cap = ?, reserved = reserved + ? "
                    "WHERE key_ref = ? AND bucket = ? AND kst_day = ?",
                    (cap, n, key_ref, bucket, today),
                )
            else:
                conn.execute(
                    "INSERT INTO quota (key_ref, bucket, kst_day, cap, reserved, used, blocked_until_utc) "
                    "VALUES (?, ?, ?, ?, ?, 0, NULL)",
                    (key_ref, bucket, today, cap, n),
                )
            conn.execute("COMMIT")
            in_tx = False
            return True
        except Exception:
            if in_tx:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def commit(self, key_ref: str, bucket: str, *, used: int, reserved: int) -> None:
        """Settle a finished call by subtracting reserved and adding used."""
        _validate_key_ref(key_ref)
        _validate_bucket(bucket)
        _validate_amount_non_negative(used)
        _validate_amount_non_negative(reserved)

        now = self._clock()
        today = kst_day(now)

        conn = sqlite3.connect(str(self._path), timeout=30.0, isolation_level=None)
        in_tx = False
        try:
            conn.execute("BEGIN IMMEDIATE")
            in_tx = True
            cur = conn.cursor()
            cur.execute(
                "SELECT cap, reserved, used FROM quota WHERE key_ref = ? AND bucket = ? AND kst_day = ?",
                (key_ref, bucket, today),
            )
            row = cur.fetchone()
            if row is None:
                if reserved > 0:
                    raise C.ContractError("quota_underflow")
                conn.execute(
                    "INSERT INTO quota (key_ref, bucket, kst_day, cap, reserved, used, blocked_until_utc) "
                    "VALUES (?, ?, ?, 0, 0, ?, NULL)",
                    (key_ref, bucket, today, used),
                )
            else:
                cur_reserved = int(row[1])
                if reserved > cur_reserved:
                    raise C.ContractError("quota_underflow")
                conn.execute(
                    "UPDATE quota SET reserved = reserved - ?, used = used + ? "
                    "WHERE key_ref = ? AND bucket = ? AND kst_day = ?",
                    (reserved, used, key_ref, bucket, today),
                )
            conn.execute("COMMIT")
            in_tx = False
        except Exception:
            if in_tx:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def release(self, key_ref: str, bucket: str, n: int) -> None:
        """Give back n reserved units of today without counting them as used."""
        _validate_key_ref(key_ref)
        _validate_bucket(bucket)
        _validate_amount_positive(n)

        now = self._clock()
        today = kst_day(now)

        conn = sqlite3.connect(str(self._path), timeout=30.0, isolation_level=None)
        in_tx = False
        try:
            conn.execute("BEGIN IMMEDIATE")
            in_tx = True
            cur = conn.cursor()
            cur.execute(
                "SELECT reserved FROM quota WHERE key_ref = ? AND bucket = ? AND kst_day = ?",
                (key_ref, bucket, today),
            )
            row = cur.fetchone()
            cur_reserved = int(row[0]) if row is not None else 0
            if n > cur_reserved:
                raise C.ContractError("quota_underflow")
            conn.execute(
                "UPDATE quota SET reserved = reserved - ? WHERE key_ref = ? AND bucket = ? AND kst_day = ?",
                (n, key_ref, bucket, today),
            )
            conn.execute("COMMIT")
            in_tx = False
        except Exception:
            if in_tx:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def block_until_reset(self, key_ref: str, bucket: str) -> str:
        """Block today's row until the next 00:00 KST and return reset instant."""
        _validate_key_ref(key_ref)
        _validate_bucket(bucket)

        now = self._clock()
        today = kst_day(now)
        reset_utc = f"{today}T15:00:00Z"

        conn = sqlite3.connect(str(self._path), timeout=30.0, isolation_level=None)
        in_tx = False
        try:
            conn.execute("BEGIN IMMEDIATE")
            in_tx = True
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM quota WHERE key_ref = ? AND bucket = ? AND kst_day = ?",
                (key_ref, bucket, today),
            )
            row = cur.fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO quota (key_ref, bucket, kst_day, cap, reserved, used, blocked_until_utc) "
                    "VALUES (?, ?, ?, 0, 0, 0, ?)",
                    (key_ref, bucket, today, reset_utc),
                )
            else:
                conn.execute(
                    "UPDATE quota SET blocked_until_utc = ? "
                    "WHERE key_ref = ? AND bucket = ? AND kst_day = ?",
                    (reset_utc, key_ref, bucket, today),
                )
            conn.execute("COMMIT")
            in_tx = False
            return reset_utc
        except Exception:
            if in_tx:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def snapshot(self, key_ref: str, bucket: str) -> dict:
        """Return today's quota snapshot dictionary for key_ref and bucket."""
        _validate_key_ref(key_ref)
        _validate_bucket(bucket)

        now = self._clock()
        today = kst_day(now)

        conn = sqlite3.connect(str(self._path), timeout=30.0, isolation_level=None)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT cap, reserved, used, blocked_until_utc FROM quota "
                "WHERE key_ref = ? AND bucket = ? AND kst_day = ?",
                (key_ref, bucket, today),
            )
            row = cur.fetchone()
            if row is None:
                return {
                    "kst_day": today,
                    "cap": 0,
                    "reserved": 0,
                    "used": 0,
                    "blocked_until_utc": None,
                }
            return {
                "kst_day": today,
                "cap": int(row[0]),
                "reserved": int(row[1]),
                "used": int(row[2]),
                "blocked_until_utc": row[3],
            }
        finally:
            conn.close()

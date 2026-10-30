from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import re

from budongi.team_collection import contract as C

FREQUENCIES: tuple[str, ...] = ("daily", "monthly", "quarterly", "yearly")
"""Accepted period frequencies."""

_KST = timezone(timedelta(hours=9))

_ISO_DATE_RE = re.compile(
    r"^([0-9]{4})(?:([-./])([0-9]{2})\2([0-9]{2})|([0-9]{2})([0-9]{2}))$"
)
_MONTHLY_RE = re.compile(r"^([0-9]{4})(?:[-./]([0-9]{2})|([0-9]{2}))$")
_YEARLY_RE = re.compile(r"^([0-9]{4})년?$")
_QUARTERLY_RE = re.compile(
    r"^(?:([0-9]{4})-?[Qq]([1-4])|([0-9]{4})[ \t]+([1-4])분기)$"
)


def utc_z(value: datetime) -> str:
    """Convert an aware datetime to UTC and return canonical UTC 'Z' string."""
    if not isinstance(value, datetime):
        raise C.ContractError("invalid_datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise C.ContractError("naive_datetime")
    try:
        utc_val = value.astimezone(timezone.utc)
    except OverflowError:
        raise C.ContractError("invalid_datetime")
    res = (
        f"{utc_val.year:04d}-{utc_val.month:02d}-{utc_val.day:02d}T"
        f"{utc_val.hour:02d}:{utc_val.minute:02d}:{utc_val.second:02d}Z"
    )
    if not C.UTC_Z_RE.match(res):
        raise C.ContractError("invalid_datetime")
    return res


def kst_to_utc_z(text: str, *, fmt: str) -> str:
    """Parse text as naive KST wall time and return canonical UTC 'Z' string."""
    if not isinstance(fmt, str) or not fmt or "%z" in fmt or "%Z" in fmt:
        raise C.ContractError("invalid_format")
    if not isinstance(text, str):
        raise C.ContractError("invalid_datetime")
    s = text.strip()
    if not s:
        raise C.ContractError("invalid_datetime")

    try:
        parsed = datetime.strptime(s, fmt)
    except (ValueError, OverflowError):
        parsed = None

    if parsed is not None:
        parsed = parsed.replace(tzinfo=_KST)
        return utc_z(parsed)

    if s.count("24:00") != 1:
        raise C.ContractError("invalid_datetime")

    candidate = s.replace("24:00", "00:00", 1)
    try:
        parsed = datetime.strptime(candidate, fmt)
    except (ValueError, OverflowError):
        raise C.ContractError("invalid_datetime")

    if (
        parsed.hour != 0
        or parsed.minute != 0
        or parsed.second != 0
        or parsed.microsecond != 0
    ):
        raise C.ContractError("invalid_datetime")

    try:
        parsed = parsed + timedelta(days=1)
    except OverflowError:
        raise C.ContractError("invalid_datetime")

    parsed = parsed.replace(tzinfo=_KST)
    return utc_z(parsed)


def iso_date(text: str | None) -> str | None:
    """Return canonical ISO date string for calendar-valid date text."""
    if text is None:
        return None
    if not isinstance(text, str):
        raise C.ContractError("invalid_date")
    s = text.strip()
    if not s:
        return None
    m = _ISO_DATE_RE.match(s)
    if not m:
        raise C.ContractError("invalid_date")
    year = m.group(1)
    if year == "0000":
        raise C.ContractError("invalid_date")
    if m.group(2) is not None:
        month = m.group(3)
        day = m.group(4)
    else:
        month = m.group(5)
        day = m.group(6)
    try:
        d = date(int(year), int(month), int(day))
    except ValueError:
        raise C.ContractError("invalid_date")
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"


def period_key(text: str, *, frequency: str) -> str:
    """Return canonical period key for text at the given frequency."""
    if frequency not in FREQUENCIES:
        raise C.ContractError("invalid_frequency")
    if not isinstance(text, str):
        raise C.ContractError("invalid_period")
    s = text.strip()
    if not s:
        raise C.ContractError("invalid_period")

    if frequency == "daily":
        try:
            res = iso_date(s)
            if res is None:
                raise C.ContractError("invalid_period")
            return res
        except C.ContractError:
            raise C.ContractError("invalid_period")

    if frequency == "monthly":
        m = _MONTHLY_RE.match(s)
        if not m:
            raise C.ContractError("invalid_period")
        year = m.group(1)
        month = m.group(2) or m.group(3)
        if year == "0000":
            raise C.ContractError("invalid_period")
        if not (1 <= int(month) <= 12):
            raise C.ContractError("invalid_period")
        return f"{year}-{month}"

    if frequency == "yearly":
        m = _YEARLY_RE.match(s)
        if not m:
            raise C.ContractError("invalid_period")
        year = m.group(1)
        if year == "0000":
            raise C.ContractError("invalid_period")
        return year

    if frequency == "quarterly":
        m = _QUARTERLY_RE.match(s)
        if not m:
            raise C.ContractError("invalid_period")
        year = m.group(1) or m.group(3)
        quarter = m.group(2) or m.group(4)
        if year == "0000":
            raise C.ContractError("invalid_period")
        return f"{year}-Q{quarter}"

    raise C.ContractError("invalid_frequency")

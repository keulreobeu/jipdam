"""Identifiers for team_collection_v1 packages."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date
import re

from budongi.team_collection import contract as C

_SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
_ALLOWED_PREFIXES = ("T", "R", "L")


def _normalize_collected(collected: object) -> str:
    if isinstance(collected, date):
        return f"{collected.year:04d}{collected.month:02d}{collected.day:02d}"
    if isinstance(collected, str) and not isinstance(collected, bool):
        if len(collected) == 8 and collected.isascii() and collected.isdigit():
            try:
                y = int(collected[:4])
                m = int(collected[4:6])
                d = int(collected[6:8])
                date(y, m, d)
                return collected
            except ValueError:
                pass
    raise C.ContractError("invalid_collected_date")


def _check_zip_part(part: object) -> None:
    if not isinstance(part, str) or isinstance(part, bool) or not part:
        raise C.ContractError("invalid_zip_part")
    if any(c in "_/\\:" or c.isspace() for c in part):
        raise C.ContractError("invalid_zip_part")


def _check_batch_id(batch_id: object) -> None:
    if not isinstance(batch_id, str) or isinstance(batch_id, bool):
        raise C.ContractError("invalid_batch_id")
    if len(batch_id) > C.BATCH_ID_MAX or not C.BATCH_ID_RE.fullmatch(batch_id):
        raise C.ContractError("invalid_batch_id")


def make_batch_id(
    slug: str,
    *,
    period: str | None = None,
    collected: date | str,
    version: int = 1,
) -> str:
    """Return the lowercase kebab batch id or raise ContractError."""
    if not isinstance(slug, str) or isinstance(slug, bool):
        raise C.ContractError("invalid_slug")
    slug_norm = slug.strip().lower().replace("_", "-")
    if not re.fullmatch(_SLUG_PATTERN, slug_norm):
        raise C.ContractError("invalid_slug")

    period_norm: str | None = None
    if period is not None:
        if not isinstance(period, str) or isinstance(period, bool):
            raise C.ContractError("invalid_period")
        period_norm = period.strip().lower().replace("_", "-")
        if not re.fullmatch(_SLUG_PATTERN, period_norm):
            raise C.ContractError("invalid_period")

    collected_str = _normalize_collected(collected)

    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise C.ContractError("invalid_version")

    if period_norm is None:
        batch_id = f"{slug_norm}-{collected_str}-v{version}"
    else:
        batch_id = f"{slug_norm}-{period_norm}-{collected_str}-v{version}"

    if len(batch_id) > C.BATCH_ID_MAX:
        raise C.ContractError("batch_id_too_long")

    return batch_id


def zip_name(
    *,
    provider: str,
    kind: str,
    region: str,
    period: str,
    collected: date | str,
    batch_id: str,
) -> str:
    """Return a validated zip filename for collection delivery or raise ContractError."""
    _check_zip_part(provider)
    _check_zip_part(kind)
    _check_zip_part(region)
    _check_zip_part(period)
    collected_str = _normalize_collected(collected)
    _check_batch_id(batch_id)
    return f"{provider}_{kind}_{region}_{period}_{collected_str}_{batch_id}.zip"


def check_ids(
    *,
    source_id: str,
    batch_id: str,
    t_id: str,
) -> None:
    """Validate source_id, batch_id and t_id or raise ContractError."""
    if not isinstance(source_id, str) or isinstance(source_id, bool) or not C.SOURCE_ID_RE.fullmatch(source_id):
        raise C.ContractError("invalid_source_id")
    _check_batch_id(batch_id)
    if not isinstance(t_id, str) or isinstance(t_id, bool) or not C.T_ID_RE.fullmatch(t_id):
        raise C.ContractError("invalid_t_id")
    return None


def next_dataset_id(
    existing: Iterable[str],
    prefix: str = C.DATASET_PREFIX,
) -> str:
    """Return the next free dataset id with prefix or raise ContractError."""
    if prefix not in _ALLOWED_PREFIXES:
        raise C.ContractError("invalid_prefix")
    max_num: int | None = None
    pattern = rf"^{prefix}([0-9]{{3}})$"
    for item in existing:
        if isinstance(item, str) and not isinstance(item, bool):
            m = re.fullmatch(pattern, item)
            if m:
                num = int(m.group(1))
                if max_num is None or num > max_num:
                    max_num = num
    next_num = 1 if max_num is None else max_num + 1
    if next_num > 999:
        raise C.ContractError("dataset_id_exhausted")
    return f"{prefix}{next_num:03d}"


def issue_id(n: int) -> str:
    """Return C.ISSUE_PREFIX followed by n zero-padded to 3 digits or raise ContractError."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 1 or n > 999:
        raise C.ContractError("invalid_issue_number")
    return f"{C.ISSUE_PREFIX}{n:03d}"

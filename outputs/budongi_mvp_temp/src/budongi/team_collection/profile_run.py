"""Batch profiling shell (L4, first half): normalized JSONL -> per-column and row metrics.

Streams rows once through the injected accumulators (H6 per column, H8 per row), with
hash-digest sets so distinct counting over millions of rows stays memory-bounded.
The workbook assembly half (P11/P12/H7/X3) is wired separately once those units land.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator

from . import contract as C

ContractError = C.ContractError


@dataclass(frozen=True)
class ProfileUnits:
    """Injected pure units: H6 ColumnAccumulator, H8 RowAccumulator, P9 rule compiler, C3 classify."""
    column_accumulator: Callable
    row_accumulator: Callable
    compile_rule: Callable
    classify_value: Callable      # (value, *, kind, extra) -> 'null' | 'semantic' | 'present'


def digest_set() -> Callable[[str], bool]:
    """first-seen test over 8-byte blake2 digests: bounded memory for millions of values."""
    seen: set[bytes] = set()

    def first(text: str) -> bool:
        key = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
        if key in seen:
            return False
        seen.add(key)
        return True

    return first


def kind_set() -> Callable[[str, str], bool]:
    """H8 seen(kind, digest) callable sharing one bounded store per accumulator."""
    seen: set[tuple[str, bytes]] = set()

    def first(kind: str, digest: str) -> bool:
        key = (kind, hashlib.blake2b(digest.encode("utf-8"), digest_size=8).digest())
        if key in seen:
            return False
        seen.add(key)
        return True

    return first


def jsonl_rows(path: Path) -> Iterator[dict]:
    """Stream one normalized JSONL file; a non-dict line is a contract violation."""
    with Path(path).open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ContractError("invalid_jsonl_record")
            yield record


def coord_ok(x: str, y: str) -> bool:
    """x=lon, y=lat inside the Korea bounds of the contract (profiling only, no CRS logic)."""
    try:
        lon, lat = float(x), float(y)
    except (TypeError, ValueError):
        return False
    return C.KOREA_LAT[0] <= lat <= C.KOREA_LAT[1] and C.KOREA_LON[0] <= lon <= C.KOREA_LON[1]


def profile_batch(rows: Iterable[dict], *, columns: list[dict], units: ProfileUnits,
                  pk: tuple[str, ...] = (), address_cols: tuple[str, ...] = (),
                  coord_cols: tuple[str, str] | None = None,
                  missing: Callable[[object], bool] | None = None) -> dict:
    """One streaming pass -> {'columns': [H6 results in config order], 'rows': H8 result}.

    columns items: {'name': str, 'kind': H6 kind, 'rule': P9 rule text or None,
    'extra': extra semantic tokens (optional)}.
    """
    if not columns:
        raise ContractError("profile_without_columns")
    accumulators, rules = [], {}
    for config in columns:
        name, kind = config["name"], config.get("kind", "text")
        extra = frozenset(config.get("extra") or ())
        rule = units.compile_rule(config["rule"]) if config.get("rule") else None
        if rule is not None:
            rules[name] = rule
        classify = units.classify_value

        def classifier(value, *, _kind=kind, _extra=extra, _classify=classify):
            return _classify(value, kind=_kind, extra=_extra)

        accumulators.append((name, units.column_accumulator(
            name, kind=kind, classify=classifier, rule=rule, distinct=digest_set())))
    missing = missing or (lambda value: value is None or (isinstance(value, str) and not value.strip()))
    row_metrics = units.row_accumulator(pk=pk, address_cols=address_cols, coord_cols=coord_cols,
                                        coord_ok=coord_ok, seen=kind_set(), missing=missing)
    total = 0
    for record in rows:
        total += 1
        failed = False
        for name, accumulator in accumulators:
            value = record.get(name)
            accumulator.add(value)
            rule = rules.get(name)
            if rule is not None and isinstance(value, str) and value.strip() and not rule(value):
                failed = True
        row_metrics.add(record, rule_failed=failed)
    return {"total": total, "columns": [accumulator.result() for _, accumulator in accumulators],
            "rows": row_metrics.result()}

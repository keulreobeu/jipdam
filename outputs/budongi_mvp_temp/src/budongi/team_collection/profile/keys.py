from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable

from budongi.team_collection import contract as C


def _is_coord_present(val: object) -> bool:
    """Return whether coordinate value is non-None, convertible to float, and finite."""
    if val is None:
        return False
    try:
        f = float(str(val))
        return math.isfinite(f)
    except (ValueError, TypeError, OverflowError):
        return False


class RowAccumulator:
    """Counts row-level key, duplicate, address and coordinate metrics over rows passed to add()."""

    def __init__(
        self,
        *,
        pk: tuple[str, ...],
        address_cols: tuple[str, ...],
        coord_cols: tuple[str, str] | None,
        coord_ok: Callable[[str, str], bool],
        seen: Callable[[str, str], bool],
        missing: Callable[[object], bool],
    ) -> None:
        """Store the column configuration and callbacks, and initialize counters to 0."""
        self._pk: tuple[str, ...] = tuple(pk)
        self._address_cols: tuple[str, ...] = tuple(address_cols)
        if coord_cols is not None:
            if isinstance(coord_cols, (str, bytes)):
                raise C.ContractError("invalid_coord_cols")
            try:
                coord_seq = tuple(coord_cols)
            except TypeError:
                raise C.ContractError("invalid_coord_cols")
            if len(coord_seq) != 2:
                raise C.ContractError("invalid_coord_cols")
            self._coord_cols: tuple[str, str] | None = (coord_seq[0], coord_seq[1])
        else:
            self._coord_cols = None

        self._coord_ok: Callable[[str, str], bool] = coord_ok
        self._seen: Callable[[str, str], bool] = seen
        self._missing: Callable[[object], bool] = missing

        self._total: int = 0
        self._full_duplicates: int = 0
        self._pk_duplicates: int = 0
        self._pk_missing: int = 0
        self._address_present: int = 0
        self._coord_present: int = 0
        self._coord_valid: int = 0
        self._rule_failed_rows: int = 0

    def add(self, row: dict, *, rule_failed: bool = False) -> None:
        """Count one row into every metric."""
        if not isinstance(row, dict):
            raise C.ContractError("invalid_row")

        self._total += 1
        if bool(rule_failed):
            self._rule_failed_rows += 1

        row_json = json.dumps(
            row,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        row_digest = hashlib.sha256(row_json.encode("utf-8")).hexdigest()
        if not bool(self._seen("row", row_digest)):
            self._full_duplicates += 1

        if self._pk:
            pk_missing = False
            for col in self._pk:
                if col not in row:
                    pk_missing = True
                else:
                    if bool(self._missing(row[col])):
                        pk_missing = True

            if pk_missing:
                self._pk_missing += 1
            else:
                pk_json = json.dumps(
                    [row[c] for c in self._pk],
                    ensure_ascii=False,
                    separators=(",", ":"),
                    default=str,
                )
                pk_digest = hashlib.sha256(pk_json.encode("utf-8")).hexdigest()
                if not bool(self._seen("pk", pk_digest)):
                    self._pk_duplicates += 1

        if self._address_cols:
            addr_present = False
            for col in self._address_cols:
                if col in row:
                    if not bool(self._missing(row[col])):
                        addr_present = True
            if addr_present:
                self._address_present += 1

        if self._coord_cols is not None:
            x_col, y_col = self._coord_cols
            if x_col in row and y_col in row:
                val_x = row[x_col]
                val_y = row[y_col]
                if _is_coord_present(val_x) and _is_coord_present(val_y):
                    self._coord_present += 1
                    if bool(self._coord_ok(str(val_x), str(val_y))):
                        self._coord_valid += 1

    def result(self) -> dict:
        """Return a new dict with all eight metric counters."""
        return {
            "total": self._total,
            "full_duplicates": self._full_duplicates,
            "pk_duplicates": self._pk_duplicates,
            "pk_missing": self._pk_missing,
            "address_present": self._address_present,
            "coord_present": self._coord_present,
            "coord_valid": self._coord_valid,
            "rule_failed_rows": self._rule_failed_rows,
        }

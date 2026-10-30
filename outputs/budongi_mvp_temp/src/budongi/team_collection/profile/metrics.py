from __future__ import annotations

import decimal
import math
import re
from typing import Callable

from budongi.team_collection import contract as C

_VALID_KINDS = frozenset({"numeric", "date", "text", "code", "coordinate"})
_VALID_CLASSIFICATIONS = frozenset({"null", "semantic", "present"})
_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


class ColumnAccumulator:
    """Streaming accumulator of profile metrics for a single column."""

    def __init__(
        self,
        name: str,
        *,
        kind: str,
        classify: Callable[[object], str],
        rule: Callable[[str], bool] | None,
        distinct: Callable[[str], bool],
    ) -> None:
        """Initialize column accumulator with name, kind, and callables."""
        if not isinstance(kind, str) or kind not in _VALID_KINDS:
            raise C.ContractError("invalid_kind")

        self._name = name
        self._kind = kind
        self._classify = classify
        self._rule = rule
        self._distinct = distinct

        self._total = 0
        self._null = 0
        self._semantic = 0
        self._distinct_count = 0
        self._examples: list[str] = []
        self._checked = 0
        self._failures = 0

        self._parsable_decimals: list[decimal.Decimal] = []
        self._min_decimal: decimal.Decimal | None = None
        self._max_decimal: decimal.Decimal | None = None

        self._date_min: str | None = None
        self._date_max: str | None = None

    def add(self, value: object) -> None:
        """Classify one cell value and update counters and statistics."""
        classification = self._classify(value)
        if not isinstance(classification, str) or classification not in _VALID_CLASSIFICATIONS:
            raise C.ContractError("invalid_classification")

        self._total += 1
        if classification == "null":
            self._null += 1
            return
        if classification == "semantic":
            self._semantic += 1
            return

        text = value if isinstance(value, str) else str(value)

        if self._distinct(text):
            self._distinct_count += 1
            if len(self._examples) < 3:
                self._examples.append(text)

        if self._kind in ("numeric", "coordinate"):
            is_parsable = False
            parsed_decimal: decimal.Decimal | None = None
            try:
                candidate = decimal.Decimal(text.strip())
                if candidate.is_finite():
                    parsed_decimal = candidate
                    is_parsable = True
            except (decimal.InvalidOperation, ValueError):
                is_parsable = False

            if is_parsable and parsed_decimal is not None:
                self._parsable_decimals.append(parsed_decimal)
                if self._min_decimal is None or parsed_decimal < self._min_decimal:
                    self._min_decimal = parsed_decimal
                if self._max_decimal is None or parsed_decimal > self._max_decimal:
                    self._max_decimal = parsed_decimal

                if self._rule is not None:
                    self._checked += 1
                    if not self._rule(text):
                        self._failures += 1
            else:
                if self._rule is not None:
                    self._checked += 1
                    self._failures += 1

        elif self._kind == "date":
            if _DATE_PREFIX_RE.match(text):
                if self._date_min is None or text < self._date_min:
                    self._date_min = text
                if self._date_max is None or text > self._date_max:
                    self._date_max = text

            if self._rule is not None:
                self._checked += 1
                if not self._rule(text):
                    self._failures += 1

        else:
            if self._rule is not None:
                self._checked += 1
                if not self._rule(text):
                    self._failures += 1

    def result(self) -> dict:
        """Return profile metrics dict with 13 keys in fixed order."""
        if self._kind in ("numeric", "coordinate"):
            if not self._parsable_decimals:
                min_val = None
                max_val = None
                mean_val = None
                median_val = None
            else:
                min_val = str(self._min_decimal)
                max_val = str(self._max_decimal)
                n = len(self._parsable_decimals)
                mean_val = round(math.fsum(float(d) for d in self._parsable_decimals) / n, 6)
                sorted_decimals = sorted(self._parsable_decimals)
                if n % 2 == 1:
                    median_dec = sorted_decimals[n // 2]
                else:
                    median_dec = (
                        sorted_decimals[n // 2 - 1] + sorted_decimals[n // 2]
                    ) / decimal.Decimal(2)
                median_val = round(float(median_dec), 6)
        elif self._kind == "date":
            min_val = self._date_min
            max_val = self._date_max
            mean_val = None
            median_val = None
        else:
            min_val = None
            max_val = None
            mean_val = None
            median_val = None

        return {
            "name": self._name,
            "total": self._total,
            "null": self._null,
            "semantic": self._semantic,
            "missing": self._null + self._semantic,
            "distinct": self._distinct_count,
            "examples": list(self._examples),
            "min": min_val,
            "max": max_val,
            "mean": mean_val,
            "median": median_val,
            "checked": self._checked,
            "failures": self._failures,
        }

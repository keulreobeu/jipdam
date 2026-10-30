from __future__ import annotations

import math
from typing import Callable

from budongi.team_collection import contract as C


def _is_number(val: object) -> bool:
    if isinstance(val, bool):
        return False
    if not isinstance(val, (int, float)):
        return False
    return math.isfinite(val)


def _is_int(val: object) -> bool:
    return isinstance(val, int) and not isinstance(val, bool)


class TokenBucket:
    """Token bucket rate limiter with an injected clock and sleep."""

    def __init__(
        self,
        rate: float,
        burst: int,
        *,
        clock: Callable[[], float],
        sleep: Callable[[float], None],
    ) -> None:
        """Initialize a full token bucket refilled at rate tokens per second."""
        if not _is_number(rate) or rate <= 0:
            raise C.ContractError("invalid_rate")
        if not _is_int(burst) or burst < 1:
            raise C.ContractError("invalid_burst")
        if not callable(clock) or not callable(sleep):
            raise C.ContractError("invalid_clock")
        self._rate: float = float(rate)
        self._burst: float = float(burst)
        self._clock: Callable[[], float] = clock
        self._sleep: Callable[[float], None] = sleep
        self._last: float = float(clock())
        self._tokens: float = float(burst)

    def acquire(self) -> float:
        """Take one token, calling sleep once when in debt, and return wait in seconds."""
        now = float(self._clock())
        elapsed = max(0.0, now - self._last)
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last = max(self._last, now)
        self._tokens -= 1.0
        if self._tokens >= 0.0:
            return 0.0
        wait = float(-self._tokens / self._rate)
        self._sleep(wait)
        return wait


class Aimd:
    """Additive-increase / multiplicative-decrease rate controller."""

    def __init__(
        self,
        start: float,
        floor: float,
        ceiling: float,
        *,
        increase_after: int = 50,
        factor: float = 0.5,
        step: float = 0.1,
    ) -> None:
        """Validate arguments and initialize the rate controller."""
        if (
            not _is_number(start)
            or not _is_number(floor)
            or not _is_number(ceiling)
            or not (0 < floor <= start <= ceiling)
            or not _is_int(increase_after)
            or increase_after < 1
            or not _is_number(factor)
            or not (0 < factor < 1)
            or not _is_number(step)
            or step <= 0
        ):
            raise C.ContractError("invalid_aimd")
        self._rate: float = float(start)
        self._floor: float = float(floor)
        self._ceiling: float = float(ceiling)
        self._increase_after: int = increase_after
        self._factor: float = float(factor)
        self._step: float = float(step)
        self._consecutive_success: int = 0

    @property
    def rate(self) -> float:
        """Return the current rate."""
        return self._rate

    def success(self) -> float:
        """Record one success, adapt rate if threshold reached, and return rate."""
        self._consecutive_success += 1
        if self._consecutive_success >= self._increase_after:
            self._rate = min(self._ceiling, self._rate + self._step)
            self._consecutive_success = 0
        return self._rate

    def failure(self) -> float:
        """Record one failure, decrease rate multiplicatively, and return rate."""
        self._rate = max(self._floor, self._rate * self._factor)
        self._consecutive_success = 0
        return self._rate

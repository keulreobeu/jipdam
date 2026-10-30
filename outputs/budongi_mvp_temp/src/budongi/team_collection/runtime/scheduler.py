from __future__ import annotations

import heapq
import math
from typing import Callable

from budongi.team_collection import contract as C
from budongi.team_collection.base import RequestSpec


def _validate_spec(spec: object) -> None:
    """Validate that spec is a RequestSpec with a valid request_id."""
    if not isinstance(spec, RequestSpec):
        raise C.ContractError("invalid_spec")
    if not isinstance(spec.request_id, str) or not C.REQUEST_ID_RE.fullmatch(spec.request_id):
        raise C.ContractError("invalid_request_id")


def _validate_time(val: object) -> None:
    """Validate that val is a finite int or float and not a bool."""
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise C.ContractError("invalid_time")
    try:
        if not math.isfinite(val):
            raise C.ContractError("invalid_time")
    except (TypeError, ValueError, OverflowError):
        raise C.ContractError("invalid_time")


class Scheduler:
    """In-memory scheduler of RequestSpec values that reads time only through the injected clock."""

    def __init__(self, clock: Callable[[], float]) -> None:
        """Store the clock; the new scheduler is empty."""
        self._clock: Callable[[], float] = clock
        self._queue: list[tuple[float, int, RequestSpec]] = []
        self._in_flight: dict[str, RequestSpec] = {}
        self._seen_ids: set[str] = set()
        self._seq: int = 0

    def push(self, spec: RequestSpec, *, not_before: float | None = None) -> None:
        """Queue a new spec that may not be handed out before not_before."""
        _validate_spec(spec)
        if not_before is not None:
            _validate_time(not_before)
        if spec.request_id in self._seen_ids:
            raise C.ContractError("duplicate_request")

        if not_before is None:
            effective_not_before = self._clock()
        else:
            effective_not_before = not_before

        seq = self._seq
        self._seq += 1
        self._seen_ids.add(spec.request_id)
        heapq.heappush(self._queue, (effective_not_before, seq, spec))

    def pop_ready(self) -> RequestSpec | None:
        """Remove and return the due queued spec with the earliest not_before; None when nothing is due."""
        now = self._clock()
        if not self._queue:
            return None
        if self._queue[0][0] <= now:
            _, _, spec = heapq.heappop(self._queue)
            self._in_flight[spec.request_id] = spec
            return spec
        return None

    def defer(self, spec: RequestSpec, until: float) -> None:
        """Put an in-flight spec back into the queue with not_before=until."""
        _validate_spec(spec)
        _validate_time(until)
        if spec.request_id not in self._in_flight:
            raise C.ContractError("not_in_flight")

        del self._in_flight[spec.request_id]
        seq = self._seq
        self._seq += 1
        heapq.heappush(self._queue, (until, seq, spec))

    def done(self, request_id: str) -> None:
        """Mark an in-flight spec as finished; it is never handed out again."""
        if request_id not in self._in_flight:
            raise C.ContractError("not_in_flight")
        del self._in_flight[request_id]

    def pending(self) -> int:
        """Number of pushed specs not yet marked done (queued plus in flight)."""
        return len(self._queue) + len(self._in_flight)

    def next_wakeup(self) -> float | None:
        """Smallest not_before among queued specs, or None when the queue is empty."""
        if not self._queue:
            return None
        return self._queue[0][0]

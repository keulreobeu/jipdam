"""Frozen value objects shared by adapters, runtime, readers and normalizers."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestSpec:
    request_id: str                 # unique in a batch; matches contract.REQUEST_ID_RE
    lane: str                       # contract.LANES
    origin: str                     # scheme://host[:port]; keys host slots and rate limits
    url_template: str               # may contain "{KEY}"; resolved only inside transport
    params: tuple = ()              # ((name, value), ...); never auth parameters
    method: str = "GET"
    form: tuple = ()                # ((name, value), ...) for POST downloads
    headers: tuple = ()             # ((name, value), ...) e.g. Referer for portal downloads
    credential_ref: str | None = None   # service name mapped to a vault credential ID
    quota_bucket: str | None = None     # e.g. "datagokr:15000193"
    section: str = ""
    expected_rows: int | None = None
    expected_kind: str = "any"      # zip | xlsx | xls | csv | json | xml | any


@dataclass(frozen=True)
class ParsedPage:
    rows: tuple
    total: int | None
    status: str                     # ok | empty


@dataclass(frozen=True)
class Verdict:
    kind: str   # ok | empty | quota_daily | rate | transient | auth | request_error | api_response_error
    code: str


@dataclass(frozen=True)
class RawRow:
    section: str
    position: int                   # CSV data-row ordinal, XLSX sheet row, or DBF/SHP record number
    values: tuple                   # original cell texts (None for empty) in source column order
    status: str = "ok"              # ok | blank | ragged
    reason: str | None = None


@dataclass(frozen=True)
class Outcome:
    record: dict
    status: str                     # accepted | excluded | rejected
    reason: str | None = None


@dataclass(frozen=True)
class Cell:
    value: object
    formula: str | None = None
    number_format: str | None = None

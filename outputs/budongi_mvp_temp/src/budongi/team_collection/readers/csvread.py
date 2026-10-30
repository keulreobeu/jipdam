from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Iterator

from budongi.team_collection import contract as C
from budongi.team_collection.base import RawRow


def _iter_rows(
    reader: Iterator[list[str]],
    section: str,
    header_len: int,
) -> Iterator[RawRow]:
    """Yield RawRow instances for data records after the header."""
    for position, record in enumerate(reader, start=1):
        values = tuple(None if f == "" else f for f in record)
        if len(record) == 0 or all(not f.strip() for f in record):
            yield RawRow(
                section=section,
                position=position,
                values=values,
                status="blank",
                reason="blank_row",
            )
        elif len(record) != header_len:
            yield RawRow(
                section=section,
                position=position,
                values=values,
                status="ragged",
                reason="ragged_row",
            )
        else:
            yield RawRow(
                section=section,
                position=position,
                values=values,
                status="ok",
                reason=None,
            )


def read_csv(
    path: str | Path,
    *,
    encoding: str,
    section: str,
    delimiter: str = ",",
    header_row: int = 1,
) -> tuple[tuple, Iterator[RawRow]]:
    """Decode a delimited text file strictly, returning its header and an iterator of RawRow values."""
    if isinstance(header_row, bool) or not isinstance(header_row, int) or header_row < 1:
        raise C.ContractError("invalid_header_row")
    if not isinstance(delimiter, str) or len(delimiter) != 1:
        raise C.ContractError("invalid_delimiter")

    raw_bytes = Path(path).read_bytes()

    try:
        text = raw_bytes.decode(encoding, "strict")
    except UnicodeDecodeError:
        raise C.ContractError("decode_error")
    except (LookupError, TypeError, ValueError):
        raise C.ContractError("unknown_encoding")

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)

    header_record: list[str] | None = None
    for current_row_idx, record in enumerate(reader, start=1):
        if current_row_idx == header_row:
            header_record = record
            break

    if header_record is None or len(header_record) == 0:
        raise C.ContractError("invalid_header")

    seen_headers: set[str] = set()
    for col in header_record:
        if not col.strip():
            raise C.ContractError("invalid_header")
        if col in seen_headers:
            raise C.ContractError("invalid_header")
        seen_headers.add(col)

    header = tuple(header_record)
    return header, _iter_rows(reader, section, len(header))

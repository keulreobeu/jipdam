from __future__ import annotations

import codecs
from collections.abc import Iterator
import struct

from budongi.team_collection import contract as C


def dbf_header(data: bytes | bytearray, *, encoding: str = "ascii") -> dict:
    """Validate dBASE header and field descriptors and return header metadata."""
    try:
        codecs.lookup(encoding)
    except LookupError:
        raise C.ContractError("unknown_encoding")

    if len(data) < 32:
        raise C.ContractError("invalid_dbf_header")

    version, record_count, header_length, record_length = struct.unpack_from(
        "<B3xIHH", data, 0
    )

    offset = 32
    fields: list[dict] = []
    seen_names: set[str] = set()
    t = -1

    while True:
        if offset >= len(data):
            raise C.ContractError("invalid_dbf_header")
        b = data[offset]
        if b == 0x0D:
            t = offset
            break
        if offset + 32 > len(data):
            raise C.ContractError("invalid_dbf_header")

        desc = bytes(data[offset : offset + 32])
        offset += 32

        raw_name = desc[:11]
        zero_pos = raw_name.find(b"\x00")
        if zero_pos != -1:
            raw_name = raw_name[:zero_pos]

        try:
            name = raw_name.decode(encoding, "strict")
        except UnicodeDecodeError:
            raise C.ContractError("decode_error")

        if not name.strip():
            raise C.ContractError("invalid_dbf_header")
        if name in seen_names:
            raise C.ContractError("invalid_dbf_header")
        seen_names.add(name)

        field_type = chr(desc[11])
        length = desc[16]
        decimal_count = desc[17]

        fields.append(
            {
                "name": name,
                "type": field_type,
                "length": length,
                "decimal_count": decimal_count,
            }
        )

    if not fields:
        raise C.ContractError("invalid_dbf_header")

    if header_length < t + 1:
        raise C.ContractError("invalid_dbf_header")

    if record_length != 1 + sum(f["length"] for f in fields):
        raise C.ContractError("invalid_dbf_header")

    return {
        "version": version,
        "record_count": record_count,
        "header_length": header_length,
        "record_length": record_length,
        "fields": tuple(fields),
    }


def iter_dbf(
    data: bytes | bytearray, *, encoding: str
) -> Iterator[tuple[int, bool, dict]]:
    """Validate dBASE table and return an iterator of records."""
    try:
        codecs.lookup(encoding)
    except LookupError:
        raise C.ContractError("unknown_encoding")

    hdr = dbf_header(data, encoding=encoding)

    record_count = hdr["record_count"]
    header_length = hdr["header_length"]
    record_length = hdr["record_length"]
    fields = hdr["fields"]

    required_len = header_length + record_count * record_length
    if len(data) < required_len:
        raise C.ContractError("truncated_dbf")

    records: list[tuple[int, bool, dict]] = []
    for i in range(record_count):
        rec_num = i + 1
        rec_offset = header_length + i * record_length

        flag = data[rec_offset]
        if flag == 0x20:
            deleted = False
        elif flag == 0x2A:
            deleted = True
        else:
            raise C.ContractError("invalid_dbf_record")

        values: dict[str, str | None] = {}
        field_offset = rec_offset + 1
        for f in fields:
            f_len = f["length"]
            raw_val = bytes(data[field_offset : field_offset + f_len])
            field_offset += f_len
            try:
                decoded_val = raw_val.decode(encoding, "strict")
            except UnicodeDecodeError:
                raise C.ContractError("decode_error")
            cleaned = decoded_val.strip(" \x00")
            values[f["name"]] = cleaned if cleaned != "" else None

        records.append((rec_num, deleted, values))

    return iter(records)

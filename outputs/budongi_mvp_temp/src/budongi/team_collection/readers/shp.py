from __future__ import annotations

import struct
from collections.abc import Iterator

from budongi.team_collection import contract as C

_SUPPORTED_SHAPE_TYPES: frozenset[int] = frozenset(
    {0, 1, 3, 5, 8, 11, 13, 15, 18, 21, 23, 25, 28}
)
_POINT_SHAPE_TYPES: frozenset[int] = frozenset({1, 11, 21})
_MULTIPOINT_SHAPE_TYPES: frozenset[int] = frozenset({8, 18, 28})
_POLY_SHAPE_TYPES: frozenset[int] = frozenset({3, 5, 13, 15, 23, 25})


def shp_header(data: bytes) -> dict:
    """Parse and validate the 100-byte ESRI main header."""
    if len(data) < 100:
        raise C.ContractError("invalid_shp:short_header")
    file_code, _, _, _, _, _, file_length_words = struct.unpack_from(">7i", data, 0)
    if file_code != 9994:
        raise C.ContractError("invalid_shp:file_code")
    version, shape_type = struct.unpack_from("<2i", data, 28)
    if version != 1000:
        raise C.ContractError("invalid_shp:version")
    if shape_type not in _SUPPORTED_SHAPE_TYPES:
        raise C.ContractError("invalid_shp:unsupported_shape_type")
    xmin, ymin, xmax, ymax = struct.unpack_from("<4d", data, 36)
    return {
        "file_code": file_code,
        "file_length_bytes": file_length_words * 2,
        "version": version,
        "shape_type": shape_type,
        "bbox": (float(xmin), float(ymin), float(xmax), float(ymax)),
    }


def iter_shp_records(shp: bytes, shx: bytes) -> Iterator[dict]:
    """Validate the .shp/.shx pair and yield one structural summary per record."""
    shp_hdr = shp_header(shp)
    shx_hdr = shp_header(shx)
    if shp_hdr["file_length_bytes"] != len(shp) or shx_hdr["file_length_bytes"] != len(shx):
        raise C.ContractError("invalid_shp:file_length")
    shx_body_length = len(shx) - 100
    if shx_body_length % 8 != 0:
        raise C.ContractError("invalid_shp:shx_length")
    if shx_hdr["shape_type"] != shp_hdr["shape_type"]:
        raise C.ContractError("invalid_shp:shx_mismatch")

    num_records = shx_body_length // 8
    shp_len = len(shp)

    for i in range(1, num_records + 1):
        shx_entry_offset = 100 + (i - 1) * 8
        offset_words, entry_content_len_words = struct.unpack_from(">2i", shx, shx_entry_offset)
        o = offset_words * 2
        if o < 0 or o + 8 > shp_len:
            raise C.ContractError("invalid_shp:truncated")
        rec_num, rec_content_len_words = struct.unpack_from(">2i", shp, o)
        if rec_num != i or rec_content_len_words != entry_content_len_words:
            raise C.ContractError("invalid_shp:record_mismatch")
        content_bytes = entry_content_len_words * 2
        if o + 8 + content_bytes > shp_len:
            raise C.ContractError("invalid_shp:truncated")
        if content_bytes < 4:
            raise C.ContractError("invalid_shp:content_length")

        c_off = o + 8
        rec_shape_type = struct.unpack_from("<i", shp, c_off)[0]
        if rec_shape_type != 0 and rec_shape_type != shp_hdr["shape_type"]:
            raise C.ContractError("invalid_shp:shape_type_mismatch")

        if rec_shape_type == 0:
            bbox: tuple[float, float, float, float] | None = None
            num_parts = 0
            num_points = 0
        elif rec_shape_type in _POINT_SHAPE_TYPES:
            if rec_shape_type == 1:
                if content_bytes < 20:
                    raise C.ContractError("invalid_shp:content_length")
            else:
                if content_bytes < 28:
                    raise C.ContractError("invalid_shp:content_length")
            x, y = struct.unpack_from("<2d", shp, c_off + 4)
            bbox = (float(x), float(y), float(x), float(y))
            num_parts = 0
            num_points = 1
        elif rec_shape_type in _MULTIPOINT_SHAPE_TYPES:
            if content_bytes < 40:
                raise C.ContractError("invalid_shp:content_length")
            xmin, ymin, xmax, ymax, num_points = struct.unpack_from("<4di", shp, c_off + 4)
            if num_points < 0:
                raise C.ContractError("invalid_shp:negative_count")
            if rec_shape_type == 8:
                min_bytes = 40 + 16 * num_points
            else:
                min_bytes = 40 + 16 * num_points + 16 + 8 * num_points
            if content_bytes < min_bytes:
                raise C.ContractError("invalid_shp:content_length")
            bbox = (float(xmin), float(ymin), float(xmax), float(ymax))
            num_parts = 0
        else:
            if content_bytes < 44:
                raise C.ContractError("invalid_shp:content_length")
            xmin, ymin, xmax, ymax, num_parts, num_points = struct.unpack_from("<4d2i", shp, c_off + 4)
            if num_parts < 0 or num_points < 0:
                raise C.ContractError("invalid_shp:negative_count")
            if rec_shape_type in (3, 5):
                min_bytes = 44 + 4 * num_parts + 16 * num_points
            else:
                min_bytes = 44 + 4 * num_parts + 16 * num_points + 16 + 8 * num_points
            if content_bytes < min_bytes:
                raise C.ContractError("invalid_shp:content_length")
            bbox = (float(xmin), float(ymin), float(xmax), float(ymax))

        yield {
            "number": i,
            "shape_type": rec_shape_type,
            "bbox": bbox,
            "num_parts": num_parts,
            "num_points": num_points,
            "offset": o,
            "content_length": content_bytes,
        }

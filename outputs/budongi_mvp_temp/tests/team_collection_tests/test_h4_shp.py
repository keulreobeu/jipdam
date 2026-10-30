from __future__ import annotations

import struct
import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.readers.shp import iter_shp_records, shp_header


def _hdr(shape: int, length_bytes: int, bbox=(0.0, 0.0, 1.0, 1.0)) -> bytes:
    return (struct.pack(">7i", 9994, 0, 0, 0, 0, 0, length_bytes // 2)
            + struct.pack("<2i8d", 1000, shape, *bbox, 0, 0, 0, 0))


def _pair(shape: int, contents: list[bytes]) -> tuple[bytes, bytes]:
    body, entries, off = b"", b"", 100
    for i, c in enumerate(contents, 1):
        body += struct.pack(">2i", i, len(c) // 2) + c
        entries += struct.pack(">2i", off // 2, len(c) // 2)
        off += 8 + len(c)
    shp = _hdr(shape, 100 + len(body)) + body
    shx = _hdr(shape, 100 + len(entries)) + entries
    return shp, shx


def _point(x: float, y: float) -> bytes:
    return struct.pack("<i2d", 1, x, y)


def _poly(t, bbox, parts, pts) -> bytes:
    out = struct.pack("<i4d2i", t, *bbox, len(parts), len(pts))
    out += struct.pack("<%di" % len(parts), *parts)
    for x, y in pts:
        out += struct.pack("<2d", x, y)
    return out


class ShpVisibleTests(unittest.TestCase):
    def assertCode(self, code, fn, *args):
        with self.assertRaises(C.ContractError) as cm:
            fn(*args)
        self.assertEqual(str(cm.exception), code)

    def test_header_example(self):
        data = (struct.pack(">7i", 9994, 0, 0, 0, 0, 0, 50)
                + struct.pack("<2i8d", 1000, 5, 126.5, 37.25, 127.5, 37.75, 0, 0, 0, 0))
        self.assertEqual(shp_header(data), {
            "file_code": 9994, "file_length_bytes": 100, "version": 1000,
            "shape_type": 5, "bbox": (126.5, 37.25, 127.5, 37.75)})

    def test_header_short(self):
        self.assertCode("invalid_shp:short_header", shp_header, b"")

    def test_point_records(self):
        shp, shx = _pair(1, [_point(127.0, 37.5), _point(126.9, 37.6)])
        recs = list(iter_shp_records(shp, shx))
        self.assertEqual(recs, [
            {"number": 1, "shape_type": 1, "bbox": (127.0, 37.5, 127.0, 37.5),
             "num_parts": 0, "num_points": 1, "offset": 100, "content_length": 20},
            {"number": 2, "shape_type": 1, "bbox": (126.9, 37.6, 126.9, 37.6),
             "num_parts": 0, "num_points": 1, "offset": 128, "content_length": 20},
        ])

    def test_polygon_record(self):
        c = _poly(5, (1.0, 2.0, 3.0, 4.0), [0], [(1, 2), (3, 2), (3, 4), (1, 2)])
        shp, shx = _pair(5, [c])
        (rec,) = list(iter_shp_records(shp, shx))
        self.assertEqual(rec["bbox"], (1.0, 2.0, 3.0, 4.0))
        self.assertEqual((rec["num_parts"], rec["num_points"]), (1, 4))
        self.assertEqual((rec["number"], rec["shape_type"], rec["offset"]), (1, 5, 100))
        self.assertEqual(rec["content_length"], len(c))

    def test_record_number_mismatch(self):
        shp, shx = _pair(1, [_point(1.0, 2.0)])
        shp = shp[:100] + struct.pack(">i", 2) + shp[104:]
        self.assertCode("invalid_shp:record_mismatch",
                        lambda a, b: list(iter_shp_records(a, b)), shp, shx)


if __name__ == "__main__":
    unittest.main()

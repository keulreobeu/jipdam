import struct
import unittest

from budongi.team_collection.readers.dbf import dbf_header, iter_dbf


def build(fields, records, *, count=None, version=3):
    """fields: [(name_bytes, type, length, dec)]; records: [record bytes incl. flag]."""
    hlen = 32 + 32 * len(fields) + 1
    rlen = 1 + sum(f[2] for f in fields)
    n = len(records) if count is None else count
    head = struct.pack("<B3BIHH20x", version, 124, 1, 2, n, hlen, rlen)
    desc = b"".join(struct.pack("<11sc4xBB14x", nm, t.encode(), ln, dc) for nm, t, ln, dc in fields)
    return head + desc + b"\r" + b"".join(records) + b"\x1a"


FIELDS = [(b"NAME", "C", 10, 0), (b"CNT", "N", 5, 0)]


class DbfHeaderVisibleTest(unittest.TestCase):
    def test_header_fields(self):
        d = build(FIELDS, [b" abc          12", b"*" + b" " * 15])
        h = dbf_header(d)
        self.assertEqual(h["version"], 3)
        self.assertEqual(h["record_count"], 2)
        self.assertEqual(h["header_length"], 97)
        self.assertEqual(h["record_length"], 16)
        self.assertEqual(
            h["fields"],
            (
                {"name": "NAME", "type": "C", "length": 10, "decimal_count": 0},
                {"name": "CNT", "type": "N", "length": 5, "decimal_count": 0},
            ),
        )


class IterDbfVisibleTest(unittest.TestCase):
    def test_records_and_deleted(self):
        d = build(FIELDS, [b" abc          12", b"*" + b" " * 15])
        it = iter_dbf(d, encoding="ascii")
        first = next(it)
        self.assertEqual(first, (1, False, {"NAME": "abc", "CNT": "12"}))
        self.assertEqual(list(it), [(2, True, {"NAME": None, "CNT": None})])

    def test_keys_in_descriptor_order(self):
        d = build(FIELDS, [b" x          0007"])
        rows = list(iter_dbf(d, encoding="ascii"))
        self.assertEqual(list(rows[0][2].keys()), ["NAME", "CNT"])
        self.assertEqual(rows[0][2]["CNT"], "0007")

    def test_cp949_value(self):
        v = "역삼".encode("cp949").ljust(10, b" ")
        d = build(FIELDS, [b" " + v + b"    5"])
        rows = list(iter_dbf(d, encoding="cp949"))
        self.assertEqual(rows, [(1, False, {"NAME": "역삼", "CNT": "5"})])

    def test_truncated(self):
        from budongi.team_collection.contract import ContractError
        d = build(FIELDS, [b" abc          12"], count=3)
        with self.assertRaises(ContractError) as cm:
            iter_dbf(d, encoding="ascii")
        self.assertEqual(str(cm.exception), "truncated_dbf")


if __name__ == "__main__":
    unittest.main()

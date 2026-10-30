import os
import tempfile
import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.base import RawRow
from budongi.team_collection.readers.csvread import read_csv


class _TmpMixin:
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def write(self, data: bytes) -> str:
        path = os.path.join(self._tmp.name, "f.csv")
        with open(path, "wb") as fh:
            fh.write(data)
        return path


class TestE1ReadCsvTypical(_TmpMixin, unittest.TestCase):
    def test_header_and_ok_rows(self):
        path = self.write(b"a,b\n1,2\n3,4\n")
        header, rows = read_csv(path, encoding="utf-8", section="s1")
        self.assertEqual(header, ("a", "b"))
        got = list(rows)
        self.assertEqual(len(got), 2)
        self.assertIsInstance(got[0], RawRow)
        self.assertEqual(got[0], RawRow(section="s1", position=1, values=("1", "2"),
                                        status="ok", reason=None))
        self.assertEqual(got[1].position, 2)
        self.assertEqual(got[1].values, ("3", "4"))

    def test_empty_cell_becomes_none(self):
        path = self.write(b"a,b\n1,\n")
        _, rows = read_csv(path, encoding="utf-8", section="s")
        row = list(rows)[0]
        self.assertEqual(row.values, ("1", None))
        self.assertEqual(row.status, "ok")

    def test_ragged_and_blank_rows(self):
        path = self.write(b"a,b\n1,2,3\n\n4,5\n")
        _, rows = read_csv(path, encoding="utf-8", section="s")
        got = list(rows)
        self.assertEqual([r.position for r in got], [1, 2, 3])
        self.assertEqual((got[0].status, got[0].reason), ("ragged", "ragged_row"))
        self.assertEqual(got[0].values, ("1", "2", "3"))
        self.assertEqual((got[1].status, got[1].reason), ("blank", "blank_row"))
        self.assertEqual(got[1].values, ())
        self.assertEqual((got[2].status, got[2].reason), ("ok", None))

    def test_korean_cp949(self):
        path = self.write("이름,구\n서울역,중구\n".encode("cp949"))
        header, rows = read_csv(path, encoding="cp949", section="s")
        self.assertEqual(header, ("이름", "구"))
        self.assertEqual(list(rows)[0].values, ("서울역", "중구"))

    def test_utf8_sig_bom_removed(self):
        path = self.write(b"\xef\xbb\xbfa,b\n1,2\n")
        header, _ = read_csv(path, encoding="utf-8-sig", section="s")
        self.assertEqual(header, ("a", "b"))

    def test_header_row_skips_preamble(self):
        path = self.write(b"title\nnote\na,b\n1,2\n")
        header, rows = read_csv(path, encoding="utf-8", section="s", header_row=3)
        self.assertEqual(header, ("a", "b"))
        got = list(rows)
        self.assertEqual(len(got), 1)
        self.assertEqual((got[0].position, got[0].values), (1, ("1", "2")))

    def test_custom_delimiter(self):
        path = self.write(b"a;b\n1;2\n")
        header, rows = read_csv(path, encoding="utf-8", section="s", delimiter=";")
        self.assertEqual(header, ("a", "b"))
        self.assertEqual(list(rows)[0].values, ("1", "2"))


class TestE1ReadCsvErrors(_TmpMixin, unittest.TestCase):
    def test_decode_error(self):
        path = self.write("이름\n".encode("cp949"))
        with self.assertRaises(C.ContractError) as ctx:
            read_csv(path, encoding="utf-8", section="s")
        self.assertEqual(str(ctx.exception), "decode_error")

    def test_duplicate_header(self):
        path = self.write(b"a,a\n1,2\n")
        with self.assertRaises(C.ContractError) as ctx:
            read_csv(path, encoding="utf-8", section="s")
        self.assertEqual(str(ctx.exception), "invalid_header")


if __name__ == "__main__":
    unittest.main()

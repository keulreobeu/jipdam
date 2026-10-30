from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, time
from pathlib import Path

import openpyxl

from budongi.team_collection import contract as C
from budongi.team_collection.base import RawRow
from budongi.team_collection.readers.xlsxread import cell_text, read_xlsx


def _book(folder: Path, cells: dict, title: str = "S") -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title
    for (r, c), v in cells.items():
        ws.cell(row=r, column=c, value=v)
    path = folder / "book.xlsx"
    wb.save(path)
    return path


class E2CellTextTests(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(cell_text(12), "12")
        self.assertEqual(cell_text(3.0), "3")
        self.assertEqual(cell_text(1.5), "1.5")

    def test_bool_and_none(self):
        self.assertEqual(cell_text(True), "TRUE")
        self.assertEqual(cell_text(False), "FALSE")
        self.assertIsNone(cell_text(None))
        self.assertIsNone(cell_text(""))

    def test_dates_and_times(self):
        self.assertEqual(cell_text(datetime(2024, 3, 1)), "2024-03-01")
        self.assertEqual(cell_text(datetime(2024, 3, 1, 9, 5, 7)), "2024-03-01T09:05:07")
        self.assertEqual(cell_text(time(9, 5, 7)), "09:05:07")

    def test_string_unchanged(self):
        self.assertEqual(cell_text(" 0012 "), " 0012 ")


class E2ReadXlsxTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_header_and_rows(self):
        path = _book(self.dir, {
            (1, 1): "name", (1, 2): "qty",
            (2, 1): "a", (2, 2): 1,
            (4, 1): "b", (4, 2): 2.5, (4, 3): "x",
            (5, 1): "c", (5, 2): datetime(2024, 3, 1),
        })
        header, rows = read_xlsx(path, sheet="S", header_row=1, section="sec")
        self.assertEqual(header, ("name", "qty"))
        self.assertEqual(list(rows), [
            RawRow("sec", 2, ("a", "1")),
            RawRow("sec", 3, (None, None), "blank", "blank_row"),
            RawRow("sec", 4, ("b", "2.5", "x"), "ragged", "ragged_row"),
            RawRow("sec", 5, ("c", "2024-03-01")),
        ])

    def test_short_row_padded(self):
        path = _book(self.dir, {(1, 1): "a", (1, 2): "b", (1, 3): "c", (2, 1): "x"})
        _, rows = read_xlsx(path, sheet="S", header_row=1, section="s")
        self.assertEqual(list(rows), [RawRow("s", 2, ("x", None, None))])

    def test_sheet_not_found(self):
        path = _book(self.dir, {(1, 1): "a"})
        with self.assertRaises(C.ContractError) as cm:
            read_xlsx(path, sheet="missing", header_row=1, section="s")
        self.assertEqual(str(cm.exception), "sheet_not_found")

    def test_invalid_header_row(self):
        path = _book(self.dir, {(1, 1): "a"})
        with self.assertRaises(C.ContractError) as cm:
            read_xlsx(path, sheet="S", header_row=0, section="s")
        self.assertEqual(str(cm.exception), "invalid_header_row")

    def test_duplicate_header(self):
        path = _book(self.dir, {(1, 1): "a", (1, 2): "a"})
        with self.assertRaises(C.ContractError) as cm:
            read_xlsx(path, sheet="S", header_row=1, section="s")
        self.assertEqual(str(cm.exception), "invalid_header")


if __name__ == "__main__":
    unittest.main()

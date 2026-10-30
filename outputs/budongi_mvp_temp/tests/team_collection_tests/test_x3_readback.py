import tempfile
import unittest
import zipfile
from pathlib import Path

from budongi.team_collection.xcheck.readback import (
    HEADERS, SHEET_NAMES, diff, expected_layout, readback)

NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
RNS = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
PNS = 'xmlns="http://schemas.openxmlformats.org/package/2006/relationships"'
T = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"


def rel(i, kind, target):
    return f'<Relationship Id="{i}" Type="{T}{kind}" Target="{target}"/>'


def build(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook {NS} {RNS}><sheets>'
                   '<sheet name="S1" r:id="rId1"/><sheet name="S2" r:id="rId2"/>'
                   '</sheets><calcPr fullCalcOnLoad="1"/></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", f'<Relationships {PNS}>'
                   + rel("rId1", "worksheet", "worksheets/sheet1.xml")
                   + rel("rId2", "worksheet", "worksheets/sheet2.xml") + '</Relationships>')
        z.writestr("xl/sharedStrings.xml", f'<sst {NS}><si><t>ID</t></si></sst>')
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet {NS} {RNS}><sheetViews><sheetView>'
                   '<pane topLeftCell="C6" state="frozen"/>'
                   '</sheetView></sheetViews><sheetData>'
                   '<row r="2"><c r="A2"><v>1</v></c></row>'
                   '<row r="5"><c r="A5" t="s"><v>0</v></c><c r="B5" t="inlineStr"><is><t>Rate</t></is></c></row>'
                   '<row r="6"><c r="A6"><v>7</v></c><c r="B6"><f>IF((A6)=0,&quot;n/a&quot;,1/(A6))</f><v></v></c>'
                   '<c r="C6"><f>A6*2</f><v>14</v></c></row>'
                   '</sheetData><tableParts><tablePart r:id="rT1"/></tableParts></worksheet>')
        z.writestr("xl/worksheets/_rels/sheet1.xml.rels", f'<Relationships {PNS}>'
                   + rel("rT1", "table", "../tables/table1.xml") + '</Relationships>')
        z.writestr("xl/tables/table1.xml", f'<table {NS} displayName="MetadataTable1" ref="A5:C6"/>')
        z.writestr("xl/worksheets/sheet2.xml", f'<worksheet {NS}><sheetData/></worksheet>')
    return path


class ReadbackVisibleTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = build(Path(tmp.name) / "wb.xlsx")

    def test_readback_summary(self):
        got = readback(self.path)
        self.assertEqual(got["sheets"], ["S1", "S2"])
        self.assertEqual(got["headers"], {"S1": ("ID", "Rate"), "S2": ()})
        self.assertEqual(got["formulas"], {("S1", "B6"): 'IF((A6)=0,"n/a",1/(A6))', ("S1", "C6"): "A6*2"})
        self.assertEqual(got["cached"], {("S1", "B6"): None, ("S1", "C6"): "14"})
        self.assertEqual(got["panes"], {"S1": "C6", "S2": None})
        self.assertEqual(got["tables"], {"MetadataTable1": "A5:C6"})
        self.assertIs(got["calc_full_on_load"], True)

    def test_diff_equal_and_mismatch(self):
        got = readback(self.path)
        self.assertEqual(diff(got, {"sheets": ["S1", "S2"], "panes": {"S1": "C6", "S2": None}}), [])
        self.assertEqual(diff(got, {"calc_full_on_load": False}),
                         ["calc_full_on_load: expected False, got True"])
        self.assertEqual(diff(got, {"tables": {"MetadataTable1": "A5:C7"}}),
                         ["tables['MetadataTable1']: expected 'A5:C7', got 'A5:C6'"])


class ExpectedLayoutVisibleTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(SHEET_NAMES, ("데이터셋 목록", "컬럼별 메타데이터", "데이터 품질 및 연계", "전처리 및 이슈 관리"))
        self.assertEqual(list(HEADERS), list(SHEET_NAMES))
        self.assertEqual([len(HEADERS[s]) for s in SHEET_NAMES], [29, 30, 29, 11])

    def test_layout_one_row_each(self):
        exp = expected_layout(rows={s: 1 for s in SHEET_NAMES})
        self.assertEqual(exp["sheets"], list(SHEET_NAMES))
        self.assertEqual(exp["panes"], {s: "C6" for s in SHEET_NAMES})
        self.assertEqual(exp["tables"], {"MetadataTable1": "A5:AC6", "MetadataTable2": "A5:AD6",
                                         "MetadataTable3": "A5:AC6", "MetadataTable4": "A5:K6"})
        f = exp["formulas"]
        self.assertEqual(len(f), 10)
        self.assertEqual(f[("컬럼별 메타데이터", "I6")], 'IF((G6)=0,"해당 없음",H6/(G6))')
        self.assertEqual(f[("데이터 품질 및 연계", "C6")], 'IF((S6)=0,"해당 없음",B6/(S6))')


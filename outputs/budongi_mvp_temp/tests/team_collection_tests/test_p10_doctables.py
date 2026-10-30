import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.profile.doctables import extract_tables, column_definitions

DOC = (
    "<html><body><h1>API</h1>"
    "<table><thead><tr><th>출력명</th><th>출력설명</th></tr></thead>"
    "<tbody><tr><td> SGG_CD </td><td>시군구\n  코드</td></tr>"
    "<tr><td>DEAL_AMT</td><td><span>거래</span>금액</td></tr></tbody></table>"
    "<table><tr><td>x</td></tr></table></body></html>"
)


class TestP10ExtractTables(unittest.TestCase):
    def test_basic_document(self):
        self.assertEqual(extract_tables(DOC), [
            [["출력명", "출력설명"], ["SGG_CD", "시군구 코드"], ["DEAL_AMT", "거래금액"]],
            [["x"]],
        ])

    def test_empty_string(self):
        self.assertEqual(extract_tables(""), [])

    def test_no_table(self):
        self.assertEqual(extract_tables("<p>hello</p>"), [])

    def test_unclosed_cells_and_rows(self):
        self.assertEqual(extract_tables("<table><tr><td>a<td>b<tr><td>c</table>"),
                         [[["a", "b"], ["c"]]])

    def test_entities_unescaped(self):
        self.assertEqual(extract_tables("<table><tr><td>a&amp;b</td></tr></table>"),
                         [[["a&b"]]])

    def test_invalid_html(self):
        with self.assertRaises(C.ContractError) as cm:
            extract_tables(None)
        self.assertEqual(str(cm.exception), "invalid_html")


class TestP10ColumnDefinitions(unittest.TestCase):
    def test_default_headers(self):
        tables = [[["번호", "항목명", "항목설명"], ["1", "DEAL_AMT", "거래금액"],
                   ["2", " FLOOR ", " 층 "]]]
        self.assertEqual(column_definitions(tables), {"DEAL_AMT": "거래금액", "FLOOR": "층"})

    def test_first_matching_table(self):
        tables = [[["a", "b"], ["1", "2"]],
                  [["출력명", "설명"], ["X", "엑스"]],
                  [["출력명", "설명"], ["Y", "와이"]]]
        self.assertEqual(column_definitions(tables), {"X": "엑스"})

    def test_custom_headers(self):
        tables = [[["col", "desc"], ["X", "y"]]]
        self.assertEqual(column_definitions(tables, name_headers=("col",), label_headers=("desc",)),
                         {"X": "y"})

    def test_no_match(self):
        self.assertEqual(column_definitions([[["a", "b"], ["1", "2"]]]), {})

    def test_skips_empty_name(self):
        tables = [[["출력명", "출력설명"], ["", "x"], ["A", "에이"]]]
        self.assertEqual(column_definitions(tables), {"A": "에이"})

    def test_invalid_tables(self):
        with self.assertRaises(C.ContractError) as cm:
            column_definitions("nope")
        self.assertEqual(str(cm.exception), "invalid_tables")

    def test_from_extracted(self):
        self.assertEqual(column_definitions(extract_tables(DOC)),
                         {"SGG_CD": "시군구 코드", "DEAL_AMT": "거래금액"})


if __name__ == "__main__":
    unittest.main()

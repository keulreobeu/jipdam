import datetime
import unittest

from budongi.team_collection.base import Cell
from budongi.team_collection.workbook.rows import (HEADERS, column_row, dataset_row, issue_row,
                                                   quality_row)

DS, COL, QA, ISS = "데이터셋 목록", "컬럼별 메타데이터", "데이터 품질 및 연계", "전처리 및 이슈 관리"
COL_COUNTS = ("전체행수", "NULL수", "고유값수", "이상값수", "의미상결측수", "통합결측수", "검사대상수")
QA_COUNTS = ("전체중복건수", "PK중복건수", "유효성오류건수", "전체행수", "주요키결측수", "주소보유수",
             "좌표보유수", "좌표유효수", "검사대상수")


def _col(**over):
    d = {k: 10 for k in COL_COUNTS}
    d.update({"데이터셋_ID": "T001", "컬럼명": "STN_NM", "한글명": "역명", "평균": 2.5})
    d.update(over)
    return d


def _qa(**over):
    d = {k: 3 for k in QA_COUNTS}
    d.update({"데이터셋_ID": "T001", "JOIN성공률": 0.5})
    d.update(over)
    return d


class TestP11Headers(unittest.TestCase):
    def test_sheet_names_and_sizes(self):
        self.assertEqual(list(HEADERS), [DS, COL, QA, ISS])
        self.assertEqual([len(HEADERS[k]) for k in HEADERS], [29, 30, 29, 11])

    def test_first_and_last_headers(self):
        self.assertEqual(HEADERS[DS][0], "데이터셋_ID")
        self.assertEqual(HEADERS[DS][-1], "수집기록")
        self.assertEqual(HEADERS[COL][-1], "정리본_열")
        self.assertEqual(HEADERS[QA][-1], "근거")
        self.assertEqual(HEADERS[ISS], ("이슈_ID", "데이터셋_ID", "대상컬럼", "문제유형", "상세내용", "영향도",
                                        "처리방안", "담당자", "처리상태", "처리일", "비고"))


class TestP11DatasetRow(unittest.TestCase):
    def test_typical(self):
        row = dataset_row({"데이터셋_ID": "T001", "데이터셋명": "지하철역", "전체행수": 1200,
                           "전체컬럼수": 5, "파일수": 1, "수집일": datetime.date(2026, 10, 29)}, r=6)
        self.assertEqual(len(row), 29)
        self.assertTrue(all(isinstance(c, Cell) for c in row))
        self.assertEqual(row[0], Cell("T001"))
        self.assertEqual(row[1], Cell("지하철역"))
        self.assertEqual(row[7], Cell(1200, None, "#,##0"))
        self.assertEqual(row[13], Cell(datetime.date(2026, 10, 29), None, "yyyy-mm-dd"))
        self.assertEqual(row[26], Cell("미검증"))


class TestP11ColumnRow(unittest.TestCase):
    def test_formulas_row6(self):
        row = column_row(_col(), r=6)
        self.assertEqual(len(row), 30)
        self.assertEqual(row[8], Cell(None, 'IF((G6)=0,"해당 없음",H6/(G6))', "0.00%"))
        self.assertEqual(row[10].formula, 'IF((G6-X6)=0,"해당 없음",J6/(G6-X6))')
        self.assertEqual(row[19].formula, 'IF((AA6)=0,"미검사",S6/(AA6))')
        self.assertEqual(row[24].formula, 'IF((G6)=0,"해당 없음",X6/(G6))')

    def test_counts_and_stats(self):
        row = column_row(_col(), r=6)
        self.assertEqual(row[6], Cell(10, None, "#,##0"))
        self.assertEqual(row[13], Cell(2.5, None, "#,##0.0000"))
        self.assertEqual(row[11], Cell("해당 없음"))
        self.assertEqual(row[2], Cell("역명"))


class TestP11QualityRow(unittest.TestCase):
    def test_formulas_row7(self):
        row = quality_row(_qa(), r=7)
        self.assertEqual(len(row), 29)
        self.assertEqual(row[2], Cell(None, 'IF((S7)=0,"해당 없음",B7/(S7))', "0.00%"))
        self.assertEqual(row[9].formula, 'IF((S7)=0,"해당 없음",Y7/(S7))')
        self.assertEqual(row[15], Cell(0.5, None, "0.00%"))
        self.assertEqual(row[18], Cell(3, None, "#,##0"))


class TestP11IssueRow(unittest.TestCase):
    def test_typical(self):
        row = issue_row({"이슈_ID": "T-I001", "데이터셋_ID": "T001", "문제유형": "결측",
                         "처리일": "2026-10-29"}, r=6)
        self.assertEqual(len(row), 11)
        self.assertEqual(row[0], Cell("T-I001"))
        self.assertEqual(row[3], Cell("결측"))
        self.assertEqual(row[9], Cell(datetime.date(2026, 10, 29), None, "yyyy-mm-dd"))
        self.assertEqual(row[10], Cell("해당 없음"))


if __name__ == "__main__":
    unittest.main()

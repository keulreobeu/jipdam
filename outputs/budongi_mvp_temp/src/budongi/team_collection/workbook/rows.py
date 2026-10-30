"""Metadata workbook header and row builder."""
from __future__ import annotations

import datetime
import decimal
import math
import re

from budongi.team_collection import contract as C
from budongi.team_collection.base import Cell

HEADERS: dict[str, tuple[str, ...]] = {
    "데이터셋 목록": (
        "데이터셋_ID",
        "데이터셋명",
        "분류",
        "담당자",
        "제공기관",
        "출처_URL",
        "수집방법",
        "전체행수",
        "전체컬럼수",
        "파일수",
        "파일형식",
        "인코딩",
        "데이터기준일",
        "수집일",
        "갱신주기",
        "공간범위",
        "행단위",
        "PK후보",
        "JOIN키",
        "좌표계",
        "저장위치",
        "가공상태",
        "이용조건",
        "활용목적",
        "중복관계",
        "측정근거",
        "검증상태",
        "원본해시",
        "수집기록",
    ),
    "컬럼별 메타데이터": (
        "데이터셋_ID",
        "컬럼명",
        "한글명",
        "설명",
        "물리자료형",
        "논리자료형",
        "전체행수",
        "NULL수",
        "NULL비율",
        "고유값수",
        "고유값비율",
        "최솟값",
        "최댓값",
        "평균",
        "중앙값",
        "대표값",
        "단위",
        "허용값_코드",
        "이상값수",
        "이상값비율",
        "키구분",
        "전처리필요여부",
        "의미상결측수",
        "통합결측수",
        "통합결측률",
        "시트_원본위치",
        "검사대상수",
        "유효성검사규칙",
        "측정근거",
        "정리본_열",
    ),
    "데이터 품질 및 연계": (
        "데이터셋_ID",
        "전체중복건수",
        "전체중복률",
        "PK중복건수",
        "PK중복률",
        "유효성오류건수",
        "주요키결측률",
        "주소보유율",
        "좌표보유율",
        "좌표유효율",
        "공간정보형식",
        "좌표계",
        "행정구역기준",
        "연결대상",
        "JOIN키_방식",
        "JOIN성공률",
        "미연결건수",
        "기준시점일치여부",
        "전체행수",
        "중복판정기준",
        "키기준",
        "주요키결측수",
        "주소보유수",
        "좌표보유수",
        "좌표유효수",
        "검사대상수",
        "검사규칙",
        "검증상태",
        "근거",
    ),
    "전처리 및 이슈 관리": (
        "이슈_ID",
        "데이터셋_ID",
        "대상컬럼",
        "문제유형",
        "상세내용",
        "영향도",
        "처리방안",
        "담당자",
        "처리상태",
        "처리일",
        "비고",
    ),
}
"""Dict of the 4 sheet names to their exact header tuples."""

_REQUIRED_COUNTS: dict[str, frozenset[str]] = {
    "데이터셋 목록": frozenset({"전체행수", "전체컬럼수", "파일수"}),
    "컬럼별 메타데이터": frozenset(
        {"전체행수", "NULL수", "고유값수", "이상값수", "의미상결측수", "통합결측수", "검사대상수"}
    ),
    "데이터 품질 및 연계": frozenset(
        {
            "전체중복건수",
            "PK중복건수",
            "유효성오류건수",
            "전체행수",
            "주요키결측수",
            "주소보유수",
            "좌표보유수",
            "좌표유효수",
            "검사대상수",
        }
    ),
    "전처리 및 이슈 관리": frozenset(),
}

_REQUIRED_TEXT: dict[str, frozenset[str]] = {
    "데이터셋 목록": frozenset({"데이터셋_ID"}),
    "컬럼별 메타데이터": frozenset({"데이터셋_ID", "컬럼명"}),
    "데이터 품질 및 연계": frozenset({"데이터셋_ID"}),
    "전처리 및 이슈 관리": frozenset({"이슈_ID", "데이터셋_ID"}),
}

_DATE_HEADERS: dict[str, frozenset[str]] = {
    "데이터셋 목록": frozenset({"데이터기준일", "수집일"}),
    "전처리 및 이슈 관리": frozenset({"처리일"}),
    "컬럼별 메타데이터": frozenset(),
    "데이터 품질 및 연계": frozenset(),
}

_STAT_HEADERS = frozenset({"최솟값", "최댓값", "평균", "중앙값"})

_PLACEHOLDERS: dict[str, str] = {
    "검증상태": "미검증",
    "측정근거": "미측정",
    "근거": "미측정",
    "중복관계": "해당 없음",
    "좌표계": "해당 없음",
    "공간정보형식": "해당 없음",
    "단위": "해당 없음",
    "허용값_코드": "해당 없음",
    "유효성검사규칙": "해당 없음",
    "검사규칙": "해당 없음",
    "연결대상": "해당 없음",
    "JOIN키_방식": "해당 없음",
    "대상컬럼": "해당 없음",
    "처리일": "해당 없음",
    "비고": "해당 없음",
}

_NUMERIC_STR_RE = re.compile(r"^-?\d+(\.\d+)?$")
_DATE_STR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _get_placeholder(header: str) -> str:
    return _PLACEHOLDERS.get(header, "미확인")


def _formula_for(sheet: str, header: str, r: int) -> str | None:
    if sheet == "컬럼별 메타데이터":
        if header == "NULL비율":
            return f'IF((G{r})=0,"해당 없음",H{r}/(G{r}))'
        if header == "고유값비율":
            return f'IF((G{r}-X{r})=0,"해당 없음",J{r}/(G{r}-X{r}))'
        if header == "이상값비율":
            return f'IF((AA{r})=0,"미검사",S{r}/(AA{r}))'
        if header == "통합결측률":
            return f'IF((G{r})=0,"해당 없음",X{r}/(G{r}))'
    elif sheet == "데이터 품질 및 연계":
        if header == "전체중복률":
            return f'IF((S{r})=0,"해당 없음",B{r}/(S{r}))'
        if header == "PK중복률":
            return f'IF((S{r})=0,"해당 없음",D{r}/(S{r}))'
        if header == "주요키결측률":
            return f'IF((S{r})=0,"해당 없음",V{r}/(S{r}))'
        if header == "주소보유율":
            return f'IF((S{r})=0,"해당 없음",W{r}/(S{r}))'
        if header == "좌표보유율":
            return f'IF((S{r})=0,"해당 없음",X{r}/(S{r}))'
        if header == "좌표유효율":
            return f'IF((S{r})=0,"해당 없음",Y{r}/(S{r}))'
    return None


def _cell_required_count(val: object, header: str) -> Cell:
    if val is None or isinstance(val, bool) or not isinstance(val, int) or val < 0:
        raise C.ContractError(f"invalid_row:{header}")
    return Cell(value=val, formula=None, number_format="#,##0")


def _cell_optional_count_unconnected(val: object) -> Cell:
    if val is None:
        return Cell(value="미측정", formula=None, number_format=None)
    if isinstance(val, bool) or not isinstance(val, int) or val < 0:
        raise C.ContractError("invalid_row:미연결건수")
    return Cell(value=val, formula=None, number_format="#,##0")


def _cell_optional_ratio_join(val: object) -> Cell:
    if val is None:
        return Cell(value="미측정", formula=None, number_format=None)
    if (
        not isinstance(val, bool)
        and isinstance(val, (int, float))
        and math.isfinite(val)
        and 0 <= val <= 1
    ):
        return Cell(value=val, formula=None, number_format="0.00%")
    raise C.ContractError("invalid_row:JOIN성공률")


def _cell_stat(val: object, header: str) -> Cell:
    if val is None:
        return Cell(value="해당 없음", formula=None, number_format=None)
    if isinstance(val, str):
        if val.strip() == "":
            return Cell(value="해당 없음", formula=None, number_format=None)
        if _NUMERIC_STR_RE.fullmatch(val):
            try:
                num = float(val)
            except (ValueError, OverflowError):
                raise C.ContractError(f"invalid_row:{header}")
            if not math.isfinite(num):
                raise C.ContractError(f"invalid_row:{header}")
            return Cell(value=num, formula=None, number_format="#,##0.0000")
        return Cell(value=val, formula=None, number_format=None)
    if isinstance(val, bool):
        raise C.ContractError(f"invalid_row:{header}")
    if isinstance(val, decimal.Decimal):
        try:
            num = float(val)
        except (ValueError, OverflowError):
            raise C.ContractError(f"invalid_row:{header}")
        if not math.isfinite(num):
            raise C.ContractError(f"invalid_row:{header}")
        return Cell(value=num, formula=None, number_format="#,##0.0000")
    if isinstance(val, (int, float)):
        if not math.isfinite(val):
            raise C.ContractError(f"invalid_row:{header}")
        return Cell(value=val, formula=None, number_format="#,##0.0000")
    raise C.ContractError(f"invalid_row:{header}")


def _cell_date(val: object, header: str, placeholder: str) -> Cell:
    if val is None:
        return Cell(value=placeholder, formula=None, number_format=None)
    if isinstance(val, str):
        if val.strip() == "":
            return Cell(value=placeholder, formula=None, number_format=None)
        if _DATE_STR_RE.fullmatch(val):
            try:
                d_val = datetime.date.fromisoformat(val)
            except ValueError:
                raise C.ContractError(f"invalid_row:{header}")
            return Cell(value=d_val, formula=None, number_format="yyyy-mm-dd")
        return Cell(value=val, formula=None, number_format=None)
    if isinstance(val, datetime.date):
        return Cell(value=val, formula=None, number_format="yyyy-mm-dd")
    raise C.ContractError(f"invalid_row:{header}")


def _cell_required_text(val: object, header: str) -> Cell:
    if not isinstance(val, str) or val.strip() == "":
        raise C.ContractError(f"invalid_row:{header}")
    return Cell(value=val, formula=None, number_format=None)


def _cell_optional_text(val: object, placeholder: str) -> Cell:
    if val is None:
        return Cell(value=placeholder, formula=None, number_format=None)
    if isinstance(val, str):
        if val.strip() == "":
            return Cell(value=placeholder, formula=None, number_format=None)
        return Cell(value=val, formula=None, number_format=None)
    if isinstance(val, (list, tuple)):
        if len(val) == 0:
            return Cell(value=placeholder, formula=None, number_format=None)
        return Cell(value=", ".join(str(x) for x in val), formula=None, number_format=None)
    return Cell(value=str(val), formula=None, number_format=None)


def _build_row(sheet_name: str, d: dict, r: int) -> list[Cell]:
    if not isinstance(d, dict):
        raise C.ContractError("invalid_row:not_dict")
    if isinstance(r, bool) or not isinstance(r, int) or r < 6:
        raise C.ContractError("invalid_row:r")
    sheet_headers = HEADERS[sheet_name]
    header_set = set(sheet_headers)
    for k in d:
        if k not in header_set:
            raise C.ContractError("invalid_row:unknown_key")

    row: list[Cell] = []
    for header in sheet_headers:
        formula = _formula_for(sheet_name, header, r)
        if formula is not None:
            row.append(Cell(value=None, formula=formula, number_format="0.00%"))
            continue

        if header in _REQUIRED_COUNTS[sheet_name]:
            row.append(_cell_required_count(d.get(header), header))
            continue

        if sheet_name == "데이터 품질 및 연계" and header == "미연결건수":
            row.append(_cell_optional_count_unconnected(d.get(header)))
            continue

        if sheet_name == "데이터 품질 및 연계" and header == "JOIN성공률":
            row.append(_cell_optional_ratio_join(d.get(header)))
            continue

        if sheet_name == "컬럼별 메타데이터" and header in _STAT_HEADERS:
            row.append(_cell_stat(d.get(header), header))
            continue

        if header in _DATE_HEADERS[sheet_name]:
            row.append(_cell_date(d.get(header), header, _get_placeholder(header)))
            continue

        if header in _REQUIRED_TEXT[sheet_name]:
            row.append(_cell_required_text(d.get(header), header))
            continue

        row.append(_cell_optional_text(d.get(header), _get_placeholder(header)))

    return row


def dataset_row(d: dict, *, r: int) -> list[Cell]:
    """Return the '데이터셋 목록' row for dict d at sheet row r as Cells in header order."""
    return _build_row("데이터셋 목록", d, r)


def column_row(d: dict, *, r: int) -> list[Cell]:
    """Return the '컬럼별 메타데이터' row for d at row r, ratio columns as formulas for row r."""
    return _build_row("컬럼별 메타데이터", d, r)


def quality_row(d: dict, *, r: int) -> list[Cell]:
    """Return the '데이터 품질 및 연계' row for d at row r, ratio columns as formulas for row r."""
    return _build_row("데이터 품질 및 연계", d, r)


def issue_row(d: dict, *, r: int) -> list[Cell]:
    """Return the '전처리 및 이슈 관리' row for d at row r as Cells in header order."""
    return _build_row("전처리 및 이슈 관리", d, r)

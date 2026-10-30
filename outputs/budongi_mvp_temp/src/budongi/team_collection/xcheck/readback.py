"""Read an .xlsx back into a comparable summary and diff it against an expected layout."""
from __future__ import annotations

import posixpath
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from budongi.team_collection import contract as C
from budongi.team_collection.xcheck.xlsx_cells import iter_sheet_rows, sheet_names

SHEET_NAMES = ('데이터셋 목록', '컬럼별 메타데이터', '데이터 품질 및 연계', '전처리 및 이슈 관리')

HEADERS = {
    SHEET_NAMES[0]: (
        '데이터셋_ID', '데이터셋명', '분류', '담당자', '제공기관', '출처_URL', '수집방법', '전체행수',
        '전체컬럼수', '파일수', '파일형식', '인코딩', '데이터기준일', '수집일', '갱신주기', '공간범위',
        '행단위', 'PK후보', 'JOIN키', '좌표계', '저장위치', '가공상태', '이용조건', '활용목적',
        '중복관계', '측정근거', '검증상태', '원본해시', '수집기록'),
    SHEET_NAMES[1]: (
        '데이터셋_ID', '컬럼명', '한글명', '설명', '물리자료형', '논리자료형', '전체행수', 'NULL수',
        'NULL비율', '고유값수', '고유값비율', '최솟값', '최댓값', '평균', '중앙값', '대표값', '단위',
        '허용값_코드', '이상값수', '이상값비율', '키구분', '전처리필요여부', '의미상결측수',
        '통합결측수', '통합결측률', '시트_원본위치', '검사대상수', '유효성검사규칙', '측정근거',
        '정리본_열'),
    SHEET_NAMES[2]: (
        '데이터셋_ID', '전체중복건수', '전체중복률', 'PK중복건수', 'PK중복률', '유효성오류건수',
        '주요키결측률', '주소보유율', '좌표보유율', '좌표유효율', '공간정보형식', '좌표계',
        '행정구역기준', '연결대상', 'JOIN키_방식', 'JOIN성공률', '미연결건수', '기준시점일치여부',
        '전체행수', '중복판정기준', '키기준', '주요키결측수', '주소보유수', '좌표보유수',
        '좌표유효수', '검사대상수', '검사규칙', '검증상태', '근거'),
    SHEET_NAMES[3]: (
        '이슈_ID', '데이터셋_ID', '대상컬럼', '문제유형', '상세내용', '영향도', '처리방안', '담당자',
        '처리상태', '처리일', '비고'),
}

_KEYS = ('sheets', 'headers', 'formulas', 'cached', 'panes', 'tables', 'calc_full_on_load')
_DICT_KEYS = ('headers', 'formulas', 'cached', 'panes', 'tables')


def _local(name: str) -> str:
    """Local part of a possibly namespaced tag or attribute name."""
    return name.rsplit('}', 1)[-1]


def _attr(el: ET.Element, name: str) -> str | None:
    """Attribute value matched by local name."""
    for k, v in el.attrib.items():
        if _local(k) == name:
            return v
    return None


def _children(el: ET.Element, name: str) -> list[ET.Element]:
    """Direct children matched by local name."""
    return [c for c in el if _local(c.tag) == name]


def _read_part(zf: zipfile.ZipFile, part: str, code: str) -> ET.Element:
    """Parse a zip part, raising ContractError(code) when missing or malformed."""
    try:
        data = zf.read(part)
    except KeyError:
        raise C.ContractError(code) from None
    except (zipfile.BadZipFile, OSError, RuntimeError, ValueError, EOFError):
        raise C.ContractError(code) from None
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        raise C.ContractError(code) from None


def _rels(root: ET.Element) -> dict[str, str]:
    """Map relationship Id -> Target."""
    out: dict[str, str] = {}
    for el in root.iter():
        if _local(el.tag) == 'Relationship':
            rid = _attr(el, 'Id')
            target = _attr(el, 'Target')
            if rid is not None and target is not None:
                out[rid] = target
    return out


def _resolve(base_dir: str, target: str) -> str:
    """Resolve a relationship target to a package path."""
    if target.startswith('/'):
        return posixpath.normpath(target.lstrip('/'))
    return posixpath.normpath(posixpath.join(base_dir, target))


def _col_letters(n: int) -> str:
    """1-based column number to letters."""
    s = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _pane(root: ET.Element) -> str | None:
    """Frozen pane top-left cell of the first sheetView, or None."""
    view = next((el for el in root.iter() if _local(el.tag) == 'sheetView'), None)
    if view is None:
        return None
    pane = next((c for c in view if _local(c.tag) == 'pane'), None)
    if pane is None:
        return None
    if _attr(pane, 'state') not in ('frozen', 'frozenSplit'):
        return None
    top = _attr(pane, 'topLeftCell')
    if top:
        return top
    try:
        x = int(_attr(pane, 'xSplit') or 0)
        y = int(_attr(pane, 'ySplit') or 0)
    except ValueError:
        try:
            x = int(float(_attr(pane, 'xSplit') or 0))
            y = int(float(_attr(pane, 'ySplit') or 0))
        except ValueError:
            return None
    return f'{_col_letters(x + 1)}{y + 1}'


def readback(path: Path | str) -> dict:
    """Return the read-back summary of the .xlsx at path."""
    try:
        zf_cm = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile):
        raise C.ContractError('invalid_xlsx:not_zip') from None
    zf_cm.close()
    names = sheet_names(path)
    zf_cm = zipfile.ZipFile(path)
    formulas: dict = {}
    cached: dict = {}
    panes: dict = {}
    tables: dict = {}
    with zf_cm as zf:
        wb = _read_part(zf, 'xl/workbook.xml', 'invalid_xlsx:workbook')
        calc = False
        sheet_ids: list[str | None] = []
        for el in wb.iter():
            tag = _local(el.tag)
            if tag == 'sheet':
                sheet_ids.append(_attr(el, 'id'))
            elif tag == 'calcPr':
                val = _attr(el, 'fullCalcOnLoad')
                if val is not None and val.strip().lower() in ('1', 'true'):
                    calc = True
        wb_rels = _rels(_read_part(zf, 'xl/_rels/workbook.xml.rels', 'invalid_xlsx:sheet_part'))
        for idx, name in enumerate(names):
            rid = sheet_ids[idx] if idx < len(sheet_ids) else None
            target = wb_rels.get(rid) if rid is not None else None
            if target is None:
                raise C.ContractError('invalid_xlsx:sheet_part')
            part = _resolve('xl', target)
            root = _read_part(zf, part, 'invalid_xlsx:sheet_part')
            for c in root.iter():
                if _local(c.tag) != 'c':
                    continue
                f = next((x for x in c if _local(x.tag) == 'f'), None)
                if f is None:
                    continue
                ref = c.get('r')
                if ref is None:
                    raise C.ContractError('invalid_xlsx:cell_ref')
                formulas[(name, ref)] = f.text or ''
                v = next((x for x in c if _local(x.tag) == 'v'), None)
                cached[(name, ref)] = v.text if v is not None and v.text else None
            panes[name] = _pane(root)
            part_dir = posixpath.dirname(part)
            rel_part = posixpath.join(part_dir, '_rels', posixpath.basename(part) + '.rels')
            ids = [_attr(el, 'id') for el in root.iter() if _local(el.tag) == 'tablePart']
            if ids:
                srels = _rels(_read_part(zf, rel_part, 'invalid_xlsx:table_part'))
                for tid in ids:
                    ttarget = srels.get(tid) if tid is not None else None
                    if ttarget is None:
                        raise C.ContractError('invalid_xlsx:table_part')
                    troot = _read_part(zf, _resolve(part_dir, ttarget), 'invalid_xlsx:table_part')
                    tname = _attr(troot, 'displayName')
                    if tname is None:
                        tname = _attr(troot, 'name')
                    tables[tname] = _attr(troot, 'ref')
    headers: dict = {}
    for name in names:
        row: tuple = ()
        for num, values in iter_sheet_rows(path, name):
            if num == 5:
                row = tuple(values)
                break
        headers[name] = row
    return {
        'sheets': list(names),
        'headers': headers,
        'formulas': formulas,
        'cached': cached,
        'panes': panes,
        'tables': tables,
        'calc_full_on_load': calc,
    }


def diff(actual: dict, expected: dict) -> list[str]:
    """Return one message per difference between actual and expected over expected's keys."""
    for key in expected:
        if key not in _KEYS:
            raise C.ContractError(f'unknown_diff_key:{key}')
    out: list[str] = []
    for key in _KEYS:
        if key not in expected:
            continue
        e = expected[key]
        if key in _DICT_KEYS:
            a = actual.get(key)
            if a is None:
                a = {}
            for k in sorted(set(e) | set(a)):
                if k not in a:
                    out.append(f'{key}[{k!r}]: missing')
                elif k not in e:
                    out.append(f'{key}[{k!r}]: unexpected')
                elif a[k] != e[k]:
                    out.append(f'{key}[{k!r}]: expected {e[k]!r}, got {a[k]!r}')
        else:
            a = actual.get(key)
            if a != e:
                out.append(f'{key}: expected {e!r}, got {a!r}')
    return out


def expected_layout(*, rows: dict) -> dict:
    """Return the expected readback summary (without cached) of the metadata workbook."""
    if not isinstance(rows, dict) or set(rows) != set(SHEET_NAMES):
        raise C.ContractError('invalid_rows')
    for v in rows.values():
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise C.ContractError('invalid_rows')
    formulas: dict = {}
    meta = SHEET_NAMES[1]
    for r in range(6, 6 + rows[meta]):
        formulas[(meta, f'I{r}')] = f'IF((G{r})=0,"해당 없음",H{r}/(G{r}))'
        formulas[(meta, f'K{r}')] = f'IF((G{r}-X{r})=0,"해당 없음",J{r}/(G{r}-X{r}))'
        formulas[(meta, f'T{r}')] = f'IF((AA{r})=0,"미검사",S{r}/(AA{r}))'
        formulas[(meta, f'Y{r}')] = f'IF((G{r})=0,"해당 없음",X{r}/(G{r}))'
    qual = SHEET_NAMES[2]
    for r in range(6, 6 + rows[qual]):
        for col, num in (('C', 'B'), ('E', 'D'), ('G', 'V'), ('H', 'W'), ('I', 'X'), ('J', 'Y')):
            formulas[(qual, f'{col}{r}')] = f'IF((S{r})=0,"해당 없음",{num}{r}/(S{r}))'
    tables = {}
    for i, (s, last) in enumerate(zip(SHEET_NAMES, ('AC', 'AD', 'AC', 'K')), start=1):
        tables[f'MetadataTable{i}'] = f'A5:{last}{5 + max(rows[s], 1)}'
    return {
        'sheets': list(SHEET_NAMES),
        'headers': {s: HEADERS[s] for s in SHEET_NAMES},
        'formulas': formulas,
        'panes': {s: 'C6' for s in SHEET_NAMES},
        'tables': tables,
        'calc_full_on_load': True,
    }

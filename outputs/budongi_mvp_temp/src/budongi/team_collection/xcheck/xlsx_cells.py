"""Stdlib-only XLSX cell text reader (zipfile + xml.etree) for independent cross-checks."""
from __future__ import annotations

import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator

from budongi.team_collection import contract as C

_REF_RE = re.compile(r"^[A-Z]{1,3}[1-9][0-9]*$")
_MAX_COL = 16384
_MAX_ROW = 1048576


def split_ref(ref: str) -> tuple[int, int]:
    """Return the 1-based (column, row) of an A1-style cell reference."""
    if not isinstance(ref, str) or not _REF_RE.fullmatch(ref):
        raise C.ContractError("invalid_xlsx:cell_ref")
    letters = ref.rstrip("0123456789")
    col = 0
    for ch in letters:
        col = col * 26 + (ord(ch) - 64)
    row = int(ref[len(letters):])
    if col > _MAX_COL or row > _MAX_ROW:
        raise C.ContractError("invalid_xlsx:cell_ref")
    return col, row


def _local(tag: object) -> str:
    return tag.rpartition("}")[2] if isinstance(tag, str) else ""


def _attr(el: ET.Element, name: str) -> str | None:
    for key, val in el.attrib.items():
        if key == name or (key.startswith("{") and _local(key) == name and name != "id"):
            return val
    return None


def _rel_id(el: ET.Element) -> str | None:
    for key, val in el.attrib.items():
        if key.startswith("{") and _local(key) == "id":
            return val
    return None


def _open_zip(path: Path | str) -> zipfile.ZipFile:
    try:
        return zipfile.ZipFile(path, "r")
    except zipfile.BadZipFile:
        raise C.ContractError("invalid_xlsx:not_zip") from None


def _parse(zf: zipfile.ZipFile, part: str, code: str) -> ET.Element:
    try:
        with zf.open(part) as fh:
            return ET.parse(fh).getroot()
    except ET.ParseError:
        raise C.ContractError(code) from None


def _workbook_sheets(zf: zipfile.ZipFile) -> list[tuple[str, str | None]]:
    names = set(zf.namelist())
    if "xl/workbook.xml" not in names:
        raise C.ContractError("invalid_xlsx:workbook")
    root = _parse(zf, "xl/workbook.xml", "invalid_xlsx:workbook")
    out: list[tuple[str, str | None]] = []
    for el in root.iter():
        if _local(el.tag) == "sheet":
            out.append((_attr(el, "name") or "", _rel_id(el)))
    return out


def sheet_names(path: Path | str) -> list[str]:
    """Return the worksheet names listed in xl/workbook.xml, in workbook order."""
    with _open_zip(path) as zf:
        return [n for n, _ in _workbook_sheets(zf)]


def _resolve(target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target[1:])
    return posixpath.normpath("xl/" + target)


def _text(el: ET.Element) -> str:
    parts: list[str] = []

    def walk(node: ET.Element) -> None:
        for child in node:
            name = _local(child.tag)
            if name == "rPh":
                continue
            if name == "t":
                parts.append(child.text or "")
            else:
                walk(child)

    if _local(el.tag) == "t":
        return el.text or ""
    walk(el)
    return "".join(parts)


def _shared_strings(zf: zipfile.ZipFile, rels: dict[str, tuple[str, str]]) -> list[str]:
    names = set(zf.namelist())
    part = None
    for _id, (rtype, target) in rels.items():
        if rtype.endswith("/sharedStrings"):
            part = _resolve(target)
            break
    else:
        if "xl/sharedStrings.xml" in names:
            part = "xl/sharedStrings.xml"
    if part is None or part not in names:
        raise C.ContractError("invalid_xlsx:shared_strings")
    root = _parse(zf, part, "invalid_xlsx:shared_strings")
    return [_text(si) for si in root if _local(si.tag) == "si"]


def _cell_value(cell: ET.Element, get_shared) -> str | None:
    t = cell.get("t")
    v = None
    is_el = None
    for child in cell:
        name = _local(child.tag)
        if name == "v" and v is None:
            v = child
        elif name == "is" and is_el is None:
            is_el = child
    if t == "inlineStr":
        return _text(is_el) if is_el is not None else None
    vtext = v.text if v is not None else None
    if not vtext:
        return None
    if t == "s":
        shared = get_shared()
        try:
            idx = int(vtext)
        except ValueError:
            raise C.ContractError("invalid_xlsx:shared_string_index") from None
        if idx < 0 or idx >= len(shared):
            raise C.ContractError("invalid_xlsx:shared_string_index")
        return shared[idx]
    if t == "b":
        if vtext == "1":
            return "TRUE"
        if vtext == "0":
            return "FALSE"
    return vtext


def iter_sheet_rows(path: Path | str, sheet: str) -> Iterator[tuple[int, tuple]]:
    """Yield (row_number, values) for every non-empty row of the named worksheet."""
    with _open_zip(path) as zf:
        sheets = _workbook_sheets(zf)
        match = [rid for name, rid in sheets if name == sheet]
        if not match:
            raise C.ContractError("unknown_sheet")
        rid = match[0]
        names = set(zf.namelist())
        if "xl/_rels/workbook.xml.rels" not in names:
            raise C.ContractError("invalid_xlsx:sheet_part")
        rroot = _parse(zf, "xl/_rels/workbook.xml.rels", "invalid_xlsx:sheet_part")
        rels: dict[str, tuple[str, str]] = {}
        for el in rroot.iter():
            if _local(el.tag) == "Relationship":
                rels[el.get("Id") or ""] = (el.get("Type") or "", el.get("Target") or "")
        if rid is None or rid not in rels:
            raise C.ContractError("invalid_xlsx:sheet_part")
        part = _resolve(rels[rid][1])
        if part not in names:
            raise C.ContractError("invalid_xlsx:sheet_part")

        cache: list[list[str]] = []

        def get_shared() -> list[str]:
            if not cache:
                cache.append(_shared_strings(zf, rels))
            return cache[0]

        prev_row = 0
        try:
            with zf.open(part) as fh:
                for _ev, el in ET.iterparse(fh, events=("end",)):
                    if _local(el.tag) != "row":
                        continue
                    r_attr = el.get("r")
                    if r_attr is not None:
                        try:
                            row_no = int(r_attr)
                        except ValueError:
                            raise C.ContractError("invalid_xlsx:sheet_part") from None
                    else:
                        row_no = prev_row + 1
                    prev_row = row_no
                    cells: dict[int, str | None] = {}
                    prev_col = 0
                    for c in el:
                        if _local(c.tag) != "c":
                            continue
                        ref = c.get("r")
                        col = split_ref(ref)[0] if ref is not None else prev_col + 1
                        prev_col = col
                        cells[col] = _cell_value(c, get_shared)
                    el.clear()
                    last = max((k for k, val in cells.items() if val is not None), default=0)
                    if last == 0:
                        continue
                    yield row_no, tuple(cells.get(i) for i in range(1, last + 1))
        except ET.ParseError:
            raise C.ContractError("invalid_xlsx:sheet_part") from None

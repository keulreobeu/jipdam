"""Cached formula value injection and reading for OOXML workbooks."""
from __future__ import annotations

import math
import os
from pathlib import Path
import posixpath
import re
import tempfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
import zipfile

from budongi.team_collection import contract as C

_CELL_REF_RE = re.compile(r"^[A-Z]{1,3}[1-9][0-9]*$")
_CELL_RE = re.compile(
    r"<(?P<tag>(?:\w+:)?c)\b(?P<attrs>[^>]*?)(?:/>|>(?P<body>(?:(?!<(?:\w+:)?c\b).)*?)</(?P=tag)>)",
    re.DOTALL,
)
_F_RE = re.compile(
    r"<(?P<f_tag>(?:\w+:)?f)\b(?P<f_attrs>[^>]*?)(?:/>|>(?P<f_body>.*?)</(?P=f_tag)>)",
    re.DOTALL,
)
_V_RE = re.compile(
    r"<(?P<v_tag>(?:\w+:)?v)\b[^>]*?(?:/>|>.*?</(?P=v_tag)>)",
    re.DOTALL,
)
_ATTR_R_RE = re.compile(r'\br=(?:"([^"]*)"|\'([^\']*)\')')
_ATTR_T_RE = re.compile(r'(?<=\s)t=(?:"[^"]*"|\'[^\']*\')')


def _update_start_tag(start_tag: str, t_attr: str | None) -> str:
    """Return start tag with the t attribute updated or removed."""
    t_match = _ATTR_T_RE.search(start_tag)
    if t_match:
        if t_attr is not None:
            return start_tag[:t_match.start()] + f't="{t_attr}"' + start_tag[t_match.end():]
        start = t_match.start()
        end = t_match.end()
        if start > 0 and start_tag[start - 1].isspace():
            start -= 1
        elif end < len(start_tag) - 1 and start_tag[end].isspace():
            end += 1
        return start_tag[:start] + start_tag[end:]
    if t_attr is not None:
        idx = start_tag.rfind(">")
        return start_tag[:idx] + f' t="{t_attr}"' + start_tag[idx:]
    return start_tag


def _encode_value(val: object, sheet_name: str, ref: str) -> tuple[str, str | None]:
    """Encode value for cached storage or raise ContractError on unsupported type."""
    if isinstance(val, bool):
        return ("1" if val else "0", "b")
    if isinstance(val, int):
        return (str(val), None)
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            raise C.ContractError(f"unsupported_value:{sheet_name}!{ref}")
        return (repr(val), None)
    if isinstance(val, str):
        return (escape(val), "str")
    raise C.ContractError(f"unsupported_value:{sheet_name}!{ref}")


def _resolve_target(target: str) -> str:
    """Resolve workbook relationship target to normalized zip path."""
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join("xl", target))


def _load_workbook_sheets(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    """Return ordered list of (sheet_name, part_path) from zip archive."""
    namelist = zf.namelist()
    if "xl/workbook.xml" not in namelist or "xl/_rels/workbook.xml.rels" not in namelist:
        raise C.ContractError("invalid_workbook")
    try:
        wb_root = ET.fromstring(zf.read("xl/workbook.xml"))
        rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    except ET.ParseError:
        raise C.ContractError("invalid_workbook")

    rel_map: dict[str, str] = {}
    for elem in rels_root.iter():
        if elem.tag.split("}")[-1] == "Relationship":
            rel_id = elem.attrib.get("Id")
            target = elem.attrib.get("Target")
            if rel_id and target:
                rel_map[rel_id] = target

    sheets: list[tuple[str, str]] = []
    for elem in wb_root.iter():
        if elem.tag.split("}")[-1] == "sheet":
            name = elem.attrib.get("name")
            r_id = (
                elem.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
                or elem.attrib.get("id")
                or elem.attrib.get("r:id")
            )
            if name is not None and r_id is not None:
                if r_id not in rel_map:
                    raise C.ContractError("invalid_workbook")
                part_path = _resolve_target(rel_map[r_id])
                if part_path not in namelist:
                    raise C.ContractError("invalid_workbook")
                sheets.append((name, part_path))
    return sheets


def read_cached(path: Path) -> dict:
    """Return cached values and formulas for all formula cells in the workbook."""
    if not isinstance(path, Path) or not path.is_file():
        raise C.ContractError("invalid_workbook")

    try:
        with zipfile.ZipFile(path, "r") as zf:
            sheets = _load_workbook_sheets(zf)
            result: dict[tuple[str, str], dict[str, str | None]] = {}
            for sheet_name, part_path in sheets:
                try:
                    sheet_root = ET.fromstring(zf.read(part_path))
                except ET.ParseError:
                    raise C.ContractError("invalid_workbook")
                for cell in sheet_root.iter():
                    if cell.tag.split("}")[-1] == "c":
                        f_elem = None
                        v_elem = None
                        for child in cell:
                            child_tag = child.tag.split("}")[-1]
                            if child_tag == "f":
                                f_elem = child
                            elif child_tag == "v":
                                v_elem = child
                        if f_elem is not None:
                            ref = cell.attrib.get("r")
                            if ref:
                                f_text = f_elem.text or ""
                                if (
                                    v_elem is not None
                                    and v_elem.text is not None
                                    and len(v_elem.text) > 0
                                ):
                                    v_text = v_elem.text
                                else:
                                    v_text = None
                                cell_type = cell.attrib.get("t")
                                result[(sheet_name, ref)] = {
                                    "formula": f_text,
                                    "value": v_text,
                                    "type": cell_type,
                                }
            return result
    except (zipfile.BadZipFile, OSError, KeyError):
        raise C.ContractError("invalid_workbook")


def inject_cached_values(src: Path, dst: Path, values: dict) -> int:
    """Inject cached formula values into the workbook at OOXML zip/XML level."""
    if dst.exists():
        raise C.ContractError("destination_exists")

    if not isinstance(src, Path) or not src.is_file():
        raise C.ContractError("invalid_workbook")

    try:
        src_zip = zipfile.ZipFile(src, "r")
    except (zipfile.BadZipFile, OSError):
        raise C.ContractError("invalid_workbook")

    with src_zip:
        sheets = _load_workbook_sheets(src_zip)
        sheet_name_to_part = {name: part for name, part in sheets}

        sheet_cache: dict[str, tuple[str, dict[str, tuple[re.Match, re.Match | None]]]] = {}

        def _get_sheet_cells(s_name: str) -> tuple[str, dict[str, tuple[re.Match, re.Match | None]]]:
            if s_name not in sheet_cache:
                part = sheet_name_to_part[s_name]
                try:
                    xml_bytes = src_zip.read(part)
                    xml_text = xml_bytes.decode("utf-8")
                except (KeyError, UnicodeDecodeError):
                    raise C.ContractError("invalid_workbook")

                cells: dict[str, tuple[re.Match, re.Match | None]] = {}
                for m in _CELL_RE.finditer(xml_text):
                    attrs = m.group("attrs")
                    r_m = _ATTR_R_RE.search(attrs)
                    if r_m:
                        cell_ref = r_m.group(1) or r_m.group(2)
                        body = m.group("body")
                        f_m = _F_RE.search(body) if body is not None else None
                        cells[cell_ref] = (m, f_m)
                sheet_cache[s_name] = (xml_text, cells)
            return sheet_cache[s_name]

        for target, val in values.items():
            if not isinstance(target, tuple) or len(target) != 2:
                raise C.ContractError("invalid_cell_ref:")
            sheet_name, ref = target

            if not isinstance(ref, str) or not _CELL_REF_RE.match(ref):
                raise C.ContractError(f"invalid_cell_ref:{ref}")

            if sheet_name not in sheet_name_to_part:
                raise C.ContractError(f"unknown_sheet:{sheet_name}")

            _, cells = _get_sheet_cells(sheet_name)
            if ref not in cells or cells[ref][1] is None:
                raise C.ContractError(f"cell_without_formula:{sheet_name}!{ref}")

            _encode_value(val, sheet_name, ref)

        edited_parts: dict[str, bytes] = {}
        if values:
            sheet_edits: dict[str, list[tuple[int, int, str]]] = {}
            for (sheet_name, ref), val in values.items():
                xml_text, cells = _get_sheet_cells(sheet_name)
                m, f_m = cells[ref]
                if f_m is None:
                    raise C.ContractError(f"cell_without_formula:{sheet_name}!{ref}")

                new_v_text, t_attr = _encode_value(val, sheet_name, ref)
                tag = m.group("tag")
                attrs = m.group("attrs")
                body = m.group("body")
                if body is None:
                    raise C.ContractError(f"cell_without_formula:{sheet_name}!{ref}")

                original_start_tag = f"<{tag}{attrs}>"
                new_start_tag = _update_start_tag(original_start_tag, t_attr)

                prefix_f = body[:f_m.start()]
                f_elem_str = f_m.group(0)
                suffix_f = body[f_m.end():]

                prefix_f_clean = _V_RE.sub("", prefix_f)
                suffix_f_clean = _V_RE.sub("", suffix_f)

                new_body = prefix_f_clean + f_elem_str + f"<v>{new_v_text}</v>" + suffix_f_clean
                new_cell_str = new_start_tag + new_body + f"</{tag}>"

                sheet_edits.setdefault(sheet_name, []).append((m.start(), m.end(), new_cell_str))

            for s_name, edits in sheet_edits.items():
                part = sheet_name_to_part[s_name]
                xml_text, _ = sheet_cache[s_name]
                edits.sort(key=lambda x: x[0], reverse=True)
                for start_pos, end_pos, replacement in edits:
                    xml_text = xml_text[:start_pos] + replacement + xml_text[end_pos:]
                edited_parts[part] = xml_text.encode("utf-8")

        tmp_fd, tmp_name = tempfile.mkstemp(dir=dst.parent, prefix="tmp_inj_")
        os.close(tmp_fd)
        tmp_path = Path(tmp_name)

        try:
            with zipfile.ZipFile(tmp_path, "w") as dst_zip:
                for item in src_zip.infolist():
                    name = item.filename
                    data = edited_parts[name] if name in edited_parts else src_zip.read(name)
                    zinfo = zipfile.ZipInfo(filename=name, date_time=item.date_time)
                    zinfo.compress_type = item.compress_type
                    zinfo.comment = item.comment
                    dst_zip.writestr(zinfo, data)
            os.replace(tmp_path, dst)
            tmp_path = None
        finally:
            if tmp_path is not None and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    return len(values)

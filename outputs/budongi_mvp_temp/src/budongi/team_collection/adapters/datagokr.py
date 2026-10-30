from __future__ import annotations

"""data.go.kr response parser and page counter."""

import json
import xml.etree.ElementTree as ET

from budongi.team_collection import contract as C
from budongi.team_collection.base import ParsedPage


def _localname(elem: ET.Element) -> str:
    tag = elem.tag
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _parse_json(payload: bytes) -> tuple[ParsedPage, str]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        raise C.ContractError("decode_error")

    try:
        doc = json.loads(text)
    except Exception:
        raise C.ContractError("invalid_payload")

    if not isinstance(doc, dict):
        raise C.ContractError("invalid_payload")

    if "response" not in doc:
        raise C.ContractError("invalid_payload")
    response = doc["response"]
    if not isinstance(response, dict):
        raise C.ContractError("invalid_payload")

    if "header" not in response:
        raise C.ContractError("invalid_payload")
    header = response["header"]
    if not isinstance(header, dict):
        raise C.ContractError("invalid_payload")

    if "resultCode" not in header:
        raise C.ContractError("invalid_payload")
    result_code_raw = header["resultCode"]
    if isinstance(result_code_raw, bool) or not isinstance(result_code_raw, (str, int)):
        raise C.ContractError("invalid_payload")
    code = str(result_code_raw).strip()

    rows: tuple[dict, ...] = ()
    total: int | None = None

    if "body" in response and isinstance(response["body"], dict):
        body = response["body"]

        if "items" not in body or body["items"] is None or body["items"] == "" or body["items"] == []:
            rows = ()
        elif isinstance(body["items"], dict):
            items_dict = body["items"]
            if "item" not in items_dict or items_dict["item"] is None or items_dict["item"] == "" or items_dict["item"] == []:
                rows = ()
            elif isinstance(items_dict["item"], dict):
                rows = (items_dict["item"],)
            elif isinstance(items_dict["item"], list):
                rows = tuple(items_dict["item"])
            else:
                raise C.ContractError("invalid_payload")
        elif isinstance(body["items"], list):
            rows = tuple(body["items"])
        else:
            raise C.ContractError("invalid_payload")

        for r in rows:
            if not isinstance(r, dict):
                raise C.ContractError("invalid_payload")

        if "totalCount" in body:
            raw_total = body["totalCount"]
            if isinstance(raw_total, bool):
                raise C.ContractError("invalid_payload")
            if isinstance(raw_total, int):
                if raw_total < 0:
                    raise C.ContractError("invalid_payload")
                total = raw_total
            elif isinstance(raw_total, str):
                if not (raw_total.isascii() and raw_total.isdigit()):
                    raise C.ContractError("invalid_payload")
                total = int(raw_total)
            else:
                raise C.ContractError("invalid_payload")

    status = "ok" if rows else "empty"
    return ParsedPage(rows=rows, total=total, status=status), code


def _parse_xml(stripped: bytes) -> tuple[ParsedPage, str]:
    try:
        root = ET.fromstring(stripped)
    except (ET.ParseError, SyntaxError, ValueError):
        raise C.ContractError("invalid_payload")

    root_localname = _localname(root)
    if root_localname == "OpenAPI_ServiceResponse":
        cmm_header = None
        for child in root:
            if _localname(child) == "cmmMsgHeader":
                cmm_header = child
                break
        if cmm_header is None:
            raise C.ContractError("invalid_payload")

        code_elem = None
        for child in cmm_header:
            if _localname(child) == "returnReasonCode":
                code_elem = child
                break
        if code_elem is None or code_elem.text is None:
            raise C.ContractError("invalid_payload")

        code = code_elem.text.strip()
        if not code:
            raise C.ContractError("invalid_payload")

        return ParsedPage(rows=(), total=None, status="empty"), code

    if root_localname == "response":
        header_elem = None
        body_elem = None
        for child in root:
            name = _localname(child)
            if name == "header" and header_elem is None:
                header_elem = child
            elif name == "body" and body_elem is None:
                body_elem = child

        if header_elem is None:
            raise C.ContractError("invalid_payload")

        code_elem = None
        for child in header_elem:
            if _localname(child) == "resultCode":
                code_elem = child
                break
        if code_elem is None:
            raise C.ContractError("invalid_payload")

        code = (code_elem.text or "").strip()

        row_list: list[dict] = []
        total: int | None = None

        if body_elem is not None:
            for body_child in body_elem:
                if _localname(body_child) == "items":
                    for item in body_child:
                        if _localname(item) == "item":
                            row: dict = {}
                            for field in item:
                                if isinstance(field.tag, str):
                                    row[_localname(field)] = field.text
                            row_list.append(row)

            total_elem = None
            for body_child in body_elem:
                if _localname(body_child) == "totalCount":
                    total_elem = body_child
                    break
            if total_elem is not None:
                if total_elem.text is None:
                    raise C.ContractError("invalid_payload")
                stripped_tc = total_elem.text.strip()
                if not (stripped_tc.isascii() and stripped_tc.isdigit()):
                    raise C.ContractError("invalid_payload")
                total = int(stripped_tc)

        rows = tuple(row_list)
        status = "ok" if rows else "empty"
        return ParsedPage(rows=rows, total=total, status=status), code

    raise C.ContractError("invalid_payload")


def parse_page(payload: bytes) -> tuple[ParsedPage, str]:
    """Parse one data.go.kr response of any of the three documented shapes."""
    if not isinstance(payload, bytes):
        raise C.ContractError("invalid_payload")

    stripped = payload.lstrip(b" \t\r\n")
    if not stripped:
        raise C.ContractError("invalid_payload")

    first_byte = stripped[:1]
    if first_byte == b"{":
        return _parse_json(payload)
    if first_byte == b"<":
        return _parse_xml(stripped)

    raise C.ContractError("invalid_payload")


def page_count(total: int, *, rows: int) -> int:
    """Number of pageNo pages needed to fetch total rows at rows per page."""
    if isinstance(total, bool) or not isinstance(total, int):
        raise C.ContractError("invalid_total")
    if total < 0:
        raise C.ContractError("invalid_total")
    if isinstance(rows, bool) or not isinstance(rows, int):
        raise C.ContractError("invalid_rows")
    if rows < 1:
        raise C.ContractError("invalid_rows")
    if total == 0:
        return 0
    return -(-total // rows)

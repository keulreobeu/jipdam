from __future__ import annotations

import xml.etree.ElementTree as ET

from budongi.team_collection import contract as C
from budongi.team_collection.base import ParsedPage


def _local_name(tag: object) -> str:
    """Return the localname part of an XML tag."""
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _find_child(parent: ET.Element, localname: str) -> ET.Element | None:
    """Find the first direct child element with the given localname."""
    for child in parent:
        if _local_name(child.tag) == localname:
            return child
    return None


def parse_page(payload: bytes) -> tuple[ParsedPage, str, str]:
    """Parse one TOPIS bus-API XML response into a ParsedPage and header status."""
    if not isinstance(payload, bytes):
        raise C.ContractError("invalid_payload")

    try:
        root = ET.fromstring(payload)
    except Exception:
        raise C.ContractError("invalid_payload")

    root_tag = _local_name(root.tag)

    if root_tag == "ServiceResult":
        msg_header = _find_child(root, "msgHeader")
        if msg_header is None:
            raise C.ContractError("invalid_payload")

        cd_elem = _find_child(msg_header, "headerCd")
        if cd_elem is None or cd_elem.text is None:
            raise C.ContractError("invalid_payload")
        header_cd = cd_elem.text.strip()
        if not header_cd:
            raise C.ContractError("invalid_payload")

        header_msg = ""
        msg_elem = _find_child(msg_header, "headerMsg")
        if msg_elem is not None and msg_elem.text is not None:
            stripped = msg_elem.text.strip()
            if stripped:
                header_msg = stripped

        rows: list[dict[str, str | None]] = []
        for body in root:
            if _local_name(body.tag) == "msgBody":
                for item in body:
                    if _local_name(item.tag) == "itemList":
                        row = {
                            _local_name(field.tag): field.text
                            for field in item
                            if isinstance(field.tag, str) and _local_name(field.tag)
                        }
                        rows.append(row)

        status = "ok" if rows else "empty"
        page = ParsedPage(rows=tuple(rows), total=None, status=status)
        return page, header_cd, header_msg

    if root_tag == "OpenAPI_ServiceResponse":
        cmm_header = _find_child(root, "cmmMsgHeader")
        if cmm_header is None:
            raise C.ContractError("invalid_payload")

        reason_elem = _find_child(cmm_header, "returnReasonCode")
        if reason_elem is None or reason_elem.text is None:
            raise C.ContractError("invalid_payload")
        header_cd = reason_elem.text.strip()
        if not header_cd:
            raise C.ContractError("invalid_payload")

        header_msg = ""
        auth_elem = _find_child(cmm_header, "returnAuthMsg")
        if auth_elem is not None and auth_elem.text is not None:
            stripped = auth_elem.text.strip()
            if stripped:
                header_msg = stripped

        page = ParsedPage(rows=(), total=None, status="empty")
        return page, header_cd, header_msg

    raise C.ContractError("invalid_payload")

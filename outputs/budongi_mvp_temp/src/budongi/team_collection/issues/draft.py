from __future__ import annotations

from budongi.team_collection import contract as C

ISSUE_FORM_URL: str = "https://github.com/keulreobeu/jipdam/issues/new?template=data-collection.yml"
"""GitHub Issue Form URL for data collection."""

FIELD_IDS: tuple[str, ...] = (
    "source",
    "scope",
    "status",
    "results",
    "method",
    "quality",
    "duplicates",
    "artifact",
    "drive",
)
"""Issue Form field identifiers in template order."""

STATUS_OPTIONS: tuple[str, ...] = (
    "예약",
    "수집 중",
    "부분 완료",
    "수집 완료 / 업로드 대기",
    "업로드 완료",
    "실패 / 중단",
)
"""Allowed values for status field dropdown."""

QUALITY_OPTIONS: tuple[str, ...] = (
    "실제 / 원천 미검수",
    "실제 / 원천 검수됨 (매칭·시설은 결과란에 별도 표시)",
    "합성 데모 (실제 수집 범위로 계산하지 않음)",
)
"""Allowed values for quality field dropdown."""

_SINGLE_LINE_FIELDS: frozenset[str] = frozenset(
    {"source", "scope", "status", "method", "quality", "duplicates", "drive"}
)

_RESERVATION_REQUIRED: tuple[str, ...] = (
    "source",
    "scope",
    "method",
    "quality",
    "duplicates",
)

_RESERVATION_FORBIDDEN: tuple[str, ...] = (
    "results",
    "artifact",
    "drive",
)

_BYTE_MAP: list[str] = [
    chr(i) if (
        (65 <= i <= 90)
        or (97 <= i <= 122)
        or (48 <= i <= 57)
        or i in (45, 46, 95, 126)
    ) else f"%{i:02X}"
    for i in range(256)
]


def _percent_encode(value: str) -> str:
    """Encode bytes using RFC 3986 percent-encoding for query string values."""
    return "".join(_BYTE_MAP[b] for b in value.encode("utf-8"))


def issue_title(*, source: str, kind: str, region: str, period: str) -> str:
    """Render the standard issue title from source, kind, region, and period."""
    parts = (source, kind, region, period)
    stripped: list[str] = []
    for part in parts:
        if not isinstance(part, str):
            raise C.ContractError("invalid_title_part")
        s = part.strip()
        if not s or "|" in s or "\n" in s or "\r" in s:
            raise C.ContractError("invalid_title_part")
        stripped.append(s)
    return "[수집] " + " | ".join(stripped)


def render_issue(stage: str, data: dict) -> str:
    """Render the markdown Issue body for reservation or result stage."""
    if stage not in ("reservation", "result"):
        raise C.ContractError("invalid_stage")
    if not isinstance(data, dict):
        raise C.ContractError("invalid_data")

    for key in data:
        if key not in FIELD_IDS:
            raise C.ContractError(f"unknown_field:{key}")

    if stage == "reservation":
        for fid in _RESERVATION_FORBIDDEN:
            if fid in data:
                raise C.ContractError(f"reservation_field_not_allowed:{fid}")

    for fid in FIELD_IDS:
        if fid in data:
            val = data[fid]
            if not isinstance(val, str):
                raise C.ContractError(f"invalid_field:{fid}")
            if fid in _SINGLE_LINE_FIELDS and ("\n" in val or "\r" in val):
                raise C.ContractError(f"invalid_field:{fid}")

    required = _RESERVATION_REQUIRED if stage == "reservation" else FIELD_IDS
    for fid in required:
        if fid not in data or not data[fid].strip():
            raise C.ContractError(f"missing_field:{fid}")

    if stage == "reservation":
        if "status" in data:
            st = data["status"].strip()
            if st != "예약":
                raise C.ContractError("invalid_status")
            status_val = "예약"
        else:
            status_val = "예약"
    else:
        st = data["status"].strip()
        if st not in STATUS_OPTIONS or st == "예약":
            raise C.ContractError("invalid_status")
        status_val = st

    quality_val = data["quality"].strip()
    if quality_val not in QUALITY_OPTIONS:
        raise C.ContractError("invalid_quality")

    if stage == "reservation":
        results_val = "미수집"
        artifact_val = "미생성"
        drive_val = "업로드 대기"
    else:
        results_val = data["results"].strip()
        artifact_val = data["artifact"].strip()
        drive_val = data["drive"].strip()

    body_lines = [
        "### 출처·데이터 종류",
        "",
        data["source"].strip(),
        "",
        "### 범위·담당자",
        "",
        data["scope"].strip(),
        "",
        "### 상태·결과",
        "",
        f"상태: {status_val}",
        "",
        results_val,
        "",
        "### 방법·품질",
        "",
        f"방법: {data['method'].strip()}",
        "",
        f"검수 구분: {quality_val}",
        "",
        "### 중복 확인·재개",
        "",
        data["duplicates"].strip(),
        "",
        "### 파일·해시·manifest",
        "",
        artifact_val,
        "",
        "### Drive 파일",
        "",
        drive_val,
    ]
    return "\n".join(body_lines) + "\n"


def prefill_url(fields: dict, *, title: str | None = None) -> str:
    """Generate a prefill URL for the issue form with percent-encoded query pairs."""
    if not isinstance(fields, dict):
        raise C.ContractError("invalid_data")

    if title is not None and not isinstance(title, str):
        raise C.ContractError("invalid_field:title")

    for k in fields:
        if k not in FIELD_IDS:
            raise C.ContractError(f"unknown_field:{k}")

    for fid in FIELD_IDS:
        if fid in fields:
            if not isinstance(fields[fid], str):
                raise C.ContractError(f"invalid_field:{fid}")

    if title is not None and "@" in title:
        raise C.ContractError("personal_data_in_url")

    for v in fields.values():
        if "@" in v:
            raise C.ContractError("personal_data_in_url")

    query_parts: list[str] = []
    if title is not None:
        query_parts.append(f"&title={_percent_encode(title)}")
    for fid in FIELD_IDS:
        if fid in fields:
            query_parts.append(f"&{fid}={_percent_encode(fields[fid])}")

    url = ISSUE_FORM_URL + "".join(query_parts)
    if len(url) > 8000:
        raise C.ContractError("prefill_too_long")
    return url

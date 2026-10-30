"""Provider result-code classifier for data.go.kr, Seoul open data and TOPIS."""
from __future__ import annotations

from budongi.team_collection import contract as C
from budongi.team_collection.base import Verdict

__all__ = (
    "classify_datagokr",
    "classify_seoul",
    "classify_topis",
)

_DATAGOKR_RULES: dict[str, str] = {
    "00": "ok",
    "03": "empty",
    "22": "quota_daily",
    "23": "rate",
    "01": "transient",
    "02": "transient",
    "04": "transient",
    "05": "transient",
    "99": "transient",
    "20": "auth",
    "21": "auth",
    "29": "auth",
    "30": "auth",
    "31": "auth",
    "32": "auth",
    "33": "auth",
    "10": "request_error",
    "11": "request_error",
    "12": "request_error",
}

_SEOUL_EXACT: dict[str, str] = {
    "INFO-000": "ok",
    "INFO-200": "empty",
    "INFO-100": "auth",
}

_SEOUL_PREFIX_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("ERROR-3",), "request_error"),
    (("ERROR-5", "ERROR-6"), "transient"),
)

_TOPIS_RULES: tuple[tuple[str, str], ...] = (
    ("인증키 없음", "auth"),
    ("등록되지 않은 키", "auth"),
    ("사용중지", "auth"),
    ("제한을 초과", "quota_daily"),
    ("운행 종료", "empty"),
    ("존재하지 않습니다", "empty"),
    ("실시간 정보를 읽을 수 없", "transient"),
    ("찾을 수 없습니다", "request_error"),
    ("필수 Parameter", "request_error"),
    ("1자리 이상", "request_error"),
    ("잘못된", "request_error"),
    ("시스템", "transient"),
    ("준비중", "transient"),
)


def classify_datagokr(code: str) -> Verdict:
    """Map a data.go.kr gateway/service resultCode to a Verdict."""
    if not isinstance(code, str):
        raise C.ContractError("invalid_code")
    stripped = code.strip()
    kind = _DATAGOKR_RULES.get(stripped, "api_response_error")
    return Verdict(kind, stripped)


def classify_seoul(code: str) -> Verdict:
    """Map a Seoul open-data RESULT.CODE to a Verdict."""
    if not isinstance(code, str):
        raise C.ContractError("invalid_code")
    stripped = code.strip()
    if stripped in _SEOUL_EXACT:
        return Verdict(_SEOUL_EXACT[stripped], stripped)
    for prefixes, kind in _SEOUL_PREFIX_RULES:
        if stripped.startswith(prefixes):
            return Verdict(kind, stripped)
    return Verdict("api_response_error", stripped)


def classify_topis(header_cd: str, header_msg: str) -> Verdict:
    """Map a TOPIS msgHeader headerCd plus headerMsg to a Verdict."""
    if not isinstance(header_cd, str) or not isinstance(header_msg, str):
        raise C.ContractError("invalid_code")
    cd_stripped = header_cd.strip()
    if cd_stripped == "0":
        return Verdict("ok", "0")
    msg_stripped = header_msg.strip()
    for pattern, kind in _TOPIS_RULES:
        if pattern in msg_stripped:
            return Verdict(kind, cd_stripped)
    return Verdict("api_response_error", cd_stripped)

"""Fail-closed classification of provider result codes into supervisor verdicts."""
from __future__ import annotations

from budongi.team_collection import contract as C
from budongi.team_collection.base import Verdict

_DATAGOKR: dict[str, str] = {
    "00": "ok", "0": "ok",
    "03": "empty",
    "22": "quota_daily",
    "23": "rate",
    "01": "transient", "02": "transient", "04": "transient", "05": "transient", "99": "transient",
    "20": "auth", "21": "auth", "29": "auth", "30": "auth", "31": "auth", "32": "auth", "33": "auth",
    "10": "request_error", "11": "request_error", "12": "request_error",
}

_SEOUL_EXACT: dict[str, str] = {
    "INFO-000": "ok",
    "INFO-200": "empty",
    "INFO-100": "auth",
}
_SEOUL_PREFIX: tuple[tuple[str, str], ...] = (
    ("ERROR-3", "request_error"),
    ("ERROR-5", "transient"),
    ("ERROR-6", "transient"),
)

_TOPIS_MESSAGES: tuple[tuple[str, str], ...] = (
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


def _clean(value: object) -> str:
    if not isinstance(value, str):
        raise C.ContractError("invalid_code")
    return value.strip()


def classify_datagokr(code: str) -> Verdict:
    """Map a data.go.kr resultCode to a Verdict; unknown codes fail closed."""
    text = _clean(code)
    return Verdict(_DATAGOKR.get(text, "api_response_error"), text)


def classify_seoul(code: str) -> Verdict:
    """Map a Seoul open-data RESULT.CODE to a Verdict; unknown codes fail closed."""
    text = _clean(code)
    kind = _SEOUL_EXACT.get(text)
    if kind is None:
        kind = "api_response_error"
        for prefix, prefix_kind in _SEOUL_PREFIX:
            if text.startswith(prefix):
                kind = prefix_kind
                break
    return Verdict(kind, text)


def classify_topis(header_cd: str, header_msg: str) -> Verdict:
    """Map a TOPIS headerCd and headerMsg to a Verdict; unknown messages fail closed."""
    cd = _clean(header_cd)
    msg = _clean(header_msg)
    if cd == "0":
        return Verdict("ok", cd)
    for needle, kind in _TOPIS_MESSAGES:
        if needle in msg:
            return Verdict(kind, cd)
    return Verdict("api_response_error", cd)

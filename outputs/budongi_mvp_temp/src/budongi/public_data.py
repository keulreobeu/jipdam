"""Download public transaction and subscription API responses without storing keys.

These are retrieval-time source copies, not verified 2023 historical snapshots.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable


MOLIT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
MOLIT_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
APPLYHOME_URL = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail"
APPLYHOME_MODEL_URL = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancMdl"
KEY_ENV = "DATA_GO_KR_SERVICE_KEY"
MAX_PAGES = 100
Opener = Callable[..., object]


class PublicDataError(ValueError):
    """An API response was invalid or unavailable. Messages never include the key."""


def _key() -> str:
    value = os.environ.get(KEY_ENV, "").strip()
    if not value:
        raise PublicDataError(f"Set {KEY_ENV} in the current process environment")
    # The portal can show a percent-encoded key. Decode once before urlencode.
    return urllib.parse.unquote(value)


def _request(url: str, params: dict[str, object], opener: Opener) -> bytes:
    encoded = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{url}?{encoded}", headers={"User-Agent": "budongi-mvp/0.1"})
    try:
        with opener(request, timeout=20) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise PublicDataError(f"API returned HTTP {error.code}; check approval and parameters") from None
    except urllib.error.URLError:
        raise PublicDataError("API connection failed; check network access") from None


def _molit_rows(payload: bytes) -> tuple[list[dict[str, str | None]], int]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        raise PublicDataError("MOLIT returned invalid XML") from None
    code = root.findtext(".//resultCode")
    if code not in {"00", "000"}:
        raise PublicDataError(f"MOLIT API error {code or 'unknown'}; check approval and parameters")
    items = root.findall(".//items/item")
    rows = [{child.tag: child.text for child in item} for item in items]
    total_text = root.findtext(".//totalCount")
    if total_text is None:
        raise PublicDataError("MOLIT response lacks totalCount")
    return rows, int(total_text)


def parse_molit_rental_response(payload: bytes) -> tuple[list[dict[str, str | None]], int]:
    """Parse an archived apartment-rent XML page without fetching or renaming fields.

    Returned mappings preserve the XML tag names and blank values. Rental field
    mapping and unit conversion remain gated on the detailed source contract.
    """
    return _molit_rows(payload)


def _applyhome_rows(payload: bytes) -> tuple[list[dict[str, object]], int]:
    try:
        body = json.loads(payload)
    except (ValueError, UnicodeError):
        raise PublicDataError("Applyhome returned invalid JSON") from None
    if not isinstance(body, dict):
        raise PublicDataError("Applyhome response is not an object")
    if body.get("error") or body.get("errors"):
        raise PublicDataError("Applyhome API returned an error; check approval and parameters")
    rows = body.get("data")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise PublicDataError("Applyhome response lacks a data array")
    total = body.get("matchCount", body.get("totalCount"))
    if not isinstance(total, int) or total < 0:
        raise PublicDataError("Applyhome response lacks matchCount")
    return rows, total


def fetch_molit(
    *, lawd_cd: str, deal_ymd: str, output_dir: Path, per_page: int = 1000,
    opener: Opener = urllib.request.urlopen,
) -> dict[str, object]:
    if not re.fullmatch(r"\d{5}", lawd_cd):
        raise ValueError("lawd_cd must be five digits")
    if not re.fullmatch(r"\d{6}", deal_ymd) or not 1 <= int(deal_ymd[4:]) <= 12:
        raise ValueError("deal_ymd must be YYYYMM")
    return _collect(
        source="molit_apt_trade", url=MOLIT_URL,
        filters={"LAWD_CD": lawd_cd, "DEAL_YMD": deal_ymd},
        page_size_name="numOfRows", per_page=per_page,
        output_dir=output_dir, suffix="xml", parser=_molit_rows, opener=opener,
    )


def fetch_applyhome(
    *, start_date: str, end_date: str, output_dir: Path, per_page: int = 100,
    opener: Opener = urllib.request.urlopen,
) -> dict[str, object]:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date precedes start_date")
    return _collect(
        source="applyhome_apt_announcement", url=APPLYHOME_URL,
        filters={"cond[RCRIT_PBLANC_DE::GTE]": start.isoformat(),
                 "cond[RCRIT_PBLANC_DE::LTE]": end.isoformat(), "returnType": "JSON"},
        page_size_name="perPage", per_page=per_page,
        output_dir=output_dir, suffix="json", parser=_applyhome_rows, opener=opener,
    )


def fetch_applyhome_models(
    *, house_manage_no: str, output_dir: Path, per_page: int = 100,
    opener: Opener = urllib.request.urlopen,
) -> dict[str, object]:
    if not re.fullmatch(r"\d{1,20}", house_manage_no):
        raise ValueError("house_manage_no must contain 1 to 20 digits")
    return _collect(
        source="applyhome_apt_model", url=APPLYHOME_MODEL_URL,
        filters={"cond[HOUSE_MANAGE_NO::EQ]": house_manage_no, "returnType": "JSON"},
        page_size_name="perPage", per_page=per_page,
        output_dir=output_dir, suffix="json", parser=_applyhome_rows, opener=opener,
    )


def _collect(
    *, source: str, url: str, filters: dict[str, object], page_size_name: str,
    per_page: int, output_dir: Path, suffix: str, parser: Callable,
    opener: Opener,
) -> dict[str, object]:
    if not 1 <= per_page <= 1000:
        raise ValueError("per_page must be 1 through 1000")
    key = _key()
    if output_dir.exists():
        raise FileExistsError(f"Output path already exists: {output_dir}")
    rows: list[dict[str, object]] = []
    pages: list[dict[str, object]] = []
    total = None
    for page in range(1, MAX_PAGES + 1):
        params = {**filters, "pageNo" if source.startswith("molit") else "page": page,
                  page_size_name: per_page, "serviceKey": key}
        payload = _request(url, params, opener)
        page_rows, reported_total = parser(payload)
        if total is None:
            total = reported_total
        elif reported_total != total:
            raise PublicDataError("API total count changed during pagination; retry the run")
        if page == 1:
            output_dir.mkdir(parents=True, exist_ok=False)
        page_name = f"page_{page:04d}.{suffix}"
        (output_dir / page_name).write_bytes(payload)
        pages.append({"file": page_name, "sha256": hashlib.sha256(payload).hexdigest(),
                      "rows": len(page_rows)})
        rows.extend(page_rows)
        if len(rows) >= total or not page_rows:
            break
    else:
        raise PublicDataError(f"Exceeded {MAX_PAGES} pages; use a narrower query")
    if len(rows) != total:
        raise PublicDataError(f"API returned {len(rows)} rows but reported {total}; retry the run")
    with (output_dir / "rows.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    manifest: dict[str, object] = {
        "source": source, "endpoint": url, "filters": filters,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows), "page_count": len(pages), "pages": pages,
        "status": "retrieval_time_copy_unverified",
        "note": "Contract year is not proof of the record state at that historical date.",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest

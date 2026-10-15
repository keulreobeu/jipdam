"""MOLIT retrieval-time XML archives. Offline operations never open a vault."""
from __future__ import annotations

import calendar
import hashlib
import html
import json
import math
import os
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path

from .rental_recommendation import SEOUL_DISTRICTS

VERSION = "molit_collection_v1"
SERVICES = {
    "rental": {"source": "molit_apt_rent", "provider": "molit_rental", "dataset": "15126474",
               "endpoint": "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"},
    "trade": {"source": "molit_apt_trade_general", "provider": "molit_trade", "dataset": "15126469",
              "endpoint": "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"},
    "trade-detail": {"source": "molit_apt_trade_detail", "provider": "molit_trade_detail", "dataset": "15126468",
                     "endpoint": "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"},
}
MAX_RESPONSE_BYTES = 32 * 1024 * 1024


class CollectionError(ValueError):
    """Safe error codes only; never echo transport URLs or response messages."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    # Windows readers may briefly hold a handle without FILE_SHARE_DELETE.
    # Keep the previous complete JSON visible and retry only the atomic replacement.
    for attempt in range(5):
        try:
            os.replace(temporary, path)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.05 * (2 ** attempt))


def read_json(path: Path) -> dict:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise CollectionError("invalid_manifest") from None
    if not isinstance(result, dict):
        raise CollectionError("invalid_manifest")
    return result


def safe_file(root: Path, reference: str) -> Path:
    if not isinstance(reference, str) or not reference or "\\" in reference:
        raise CollectionError("unsafe_archive_reference")
    path = Path(reference)
    if path.is_absolute() or any(p in {".", ".."} or ":" in p for p in path.parts):
        raise CollectionError("unsafe_archive_reference")
    target = root / path
    if not target.resolve().is_relative_to(root.resolve()):
        raise CollectionError("unsafe_archive_reference")
    if any(p.is_symlink() for p in [target, *target.parents] if p != root.parent):
        raise CollectionError("unsafe_archive_reference")
    return target


def queries(plan: dict):
    for service in plan["services"]:
        for code in plan["districts"]:
            for month in plan["months"]:
                yield service, code, month


def query_folder(root: Path, service: str, code: str, month: str) -> Path:
    return safe_file(root, f"raw/{service}/{code}/{month}")


def create_plan(root: Path, *, batch_id: str, snapshot_date: str, districts=None,
                services=None, months=None, observation_from: str | None = None,
                per_page: int = 1000, record_url: str = "") -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", batch_id):
        raise CollectionError("invalid_batch_id")
    try:
        cutoff = date.fromisoformat(snapshot_date)
    except (ValueError, TypeError):
        raise CollectionError("invalid_snapshot_date") from None
    if type(per_page) is not int or not 1 <= per_page <= 1000:
        raise CollectionError("invalid_page_size")
    default_start = cutoff.replace(year=cutoff.year - 1, day=min(cutoff.day,
                                   calendar.monthrange(cutoff.year - 1, cutoff.month)[1]))
    try:
        start = date.fromisoformat(observation_from) if observation_from is not None else default_start
    except (ValueError, TypeError):
        raise CollectionError("invalid_observation_start") from None
    if observation_from is not None and start.isoformat() != observation_from:
        raise CollectionError("invalid_observation_start")
    if start > cutoff:
        raise CollectionError("invalid_observation_period")
    if services is None:
        from .source_files import read_registry
        services = [s["service"] for s in read_registry()["sources"] if s.get("status") == "approved" and s.get("required")]
    services = sorted(set(services))
    districts = sorted(set(SEOUL_DISTRICTS.values() if districts is None else districts))
    if not services or any(s not in SERVICES for s in services):
        raise CollectionError("invalid_services")
    if not districts or any(c not in SEOUL_DISTRICTS.values() for c in districts):
        raise CollectionError("invalid_seoul_district")
    if months is None:
        cursor = start.replace(day=1)
        months = []
        while cursor <= cutoff:
            months.append(cursor.strftime("%Y%m"))
            cursor = date(cursor.year + cursor.month // 12, cursor.month % 12 + 1, 1)
    months = sorted(set(months))
    if not months or any(not re.fullmatch(r"\d{6}", m) or not 1 <= int(m[4:]) <= 12
                         or m > cutoff.strftime("%Y%m") for m in months):
        raise CollectionError("invalid_contract_month")
    if record_url and not re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+/issues/[1-9]\d*", record_url):
        raise CollectionError("invalid_record_url")
    plan = {"schema_version": VERSION, "batch_id": batch_id, "snapshot_date": snapshot_date,
            "observation_from": start.isoformat(), "services": services, "districts": districts,
            "months": months, "per_page": per_page, "record_url": record_url,
            "quality_status": "source_unverified"}
    path = root / "plan.json"
    if path.exists():
        if read_json(path) != plan:
            raise CollectionError("existing_plan_differs_use_new_batch")
    else:
        write_json(path, plan)
    return plan


def load_plan(root: Path) -> dict:
    plan = read_json(root / "plan.json")
    if plan.get("schema_version") != VERSION or plan.get("quality_status") != "source_unverified":
        raise CollectionError("unsupported_collection_plan")
    # Reuse the input validator without writing: the existing file must match itself.
    expected = create_plan(root, batch_id=plan.get("batch_id"), snapshot_date=plan.get("snapshot_date"),
                           services=plan.get("services"), districts=plan.get("districts"),
                           months=plan.get("months"), observation_from=plan.get("observation_from"),
                           per_page=plan.get("per_page"),
                           record_url=plan.get("record_url", ""))
    if expected != plan:
        raise CollectionError("invalid_collection_plan")
    return plan


def _identity(plan: dict, service: str, code: str, month: str) -> dict:
    return {"schema_version": VERSION, "service": service, "source": SERVICES[service]["source"],
            "endpoint": SERVICES[service]["endpoint"], "district": code, "month": month,
            "per_page": plan["per_page"]}


def load_query(root: Path, plan: dict, service: str, code: str, month: str) -> dict:
    path = query_folder(root, service, code, month) / "manifest.json"
    expected = _identity(plan, service, code, month)
    if not path.exists():
        return expected | {"status": "not_collected", "attempts": [], "pages": []}
    manifest = read_json(path)
    if any(manifest.get(k) != v for k, v in expected.items()):
        raise CollectionError("query_manifest_identity_mismatch")
    if not isinstance(manifest.get("pages"), list) or not isinstance(manifest.get("attempts"), list):
        raise CollectionError("invalid_query_manifest")
    return manifest


def parse_page(payload: bytes, *, page: int, per_page: int, code: str, month: str) -> dict:
    if len(payload) > MAX_RESPONSE_BYTES or re.search(br"<!\s*(DOCTYPE|ENTITY)", payload, re.I):
        raise CollectionError("unsafe_xml")
    try:
        tree = ET.fromstring(payload)
    except (ET.ParseError, ValueError):
        raise CollectionError("invalid_xml") from None
    result_code = tree.findtext(".//header/resultCode")
    if result_code not in {"00", "000"}:
        if result_code in {"20", "30", "31"}:
            raise CollectionError("authentication_error")
        if result_code == "22":
            raise CollectionError("daily_quota_exceeded")
        if result_code in {"01", "05", "23"}:
            raise CollectionError("transient_api_error")
        raise CollectionError("api_response_error")
    try:
        total = int(tree.findtext(".//body/totalCount", ""))
        received_page = int(tree.findtext(".//body/pageNo", ""))
        received_size = int(tree.findtext(".//body/numOfRows", ""))
    except (TypeError, ValueError):
        raise CollectionError("missing_pagination_metadata") from None
    if total < 0 or received_page != page or received_size != per_page:
        raise CollectionError("pagination_metadata_mismatch")
    rows = [{child.tag: child.text for child in item} for item in tree.findall(".//body/items/item")]
    expected_count = min(per_page, max(0, total - (page - 1) * per_page))
    if len(rows) != expected_count:
        raise CollectionError("page_row_count_mismatch")
    for row in rows:
        if (row.get("sggCd") or "").strip() != code:
            raise CollectionError("response_district_mismatch")
        try:
            actual_month = f"{int(row['dealYear']):04d}{int(row['dealMonth']):02d}"
        except (KeyError, TypeError, ValueError):
            raise CollectionError("response_contract_month_missing") from None
        if actual_month != month:
            raise CollectionError("response_contract_month_mismatch")
    return {"rows": rows, "total": total, "page": received_page, "per_page": received_size}


def verify_query(folder: Path, manifest: dict, *, require_complete: bool = False) -> list[dict]:
    parsed = []
    seen = set()
    total = None
    for item in manifest["pages"]:
        number = item.get("page")
        if type(number) is not int or number < 1 or number in seen:
            raise CollectionError("duplicate_or_invalid_page")
        seen.add(number)
        path = safe_file(folder, item.get("file"))
        if not path.is_file() or digest_file(path) != item.get("sha256"):
            raise CollectionError("archive_integrity_failed")
        page = parse_page(path.read_bytes(), page=number, per_page=manifest["per_page"],
                          code=manifest["district"], month=manifest["month"])
        if len(page["rows"]) != item.get("rows") or page["total"] != item.get("total"):
            raise CollectionError("manifest_row_count_mismatch")
        if total is not None and total != page["total"]:
            raise CollectionError("pagination_total_changed")
        total = page["total"]
        parsed.append(item | {"raw_rows": page["rows"]})
    if require_complete or manifest.get("status") == "complete":
        required = max(1, math.ceil(total / manifest["per_page"])) if total is not None else 0
        if not required or seen != set(range(1, required + 1)):
            raise CollectionError("incomplete_query")
        if sum(p["rows"] for p in parsed) != total:
            raise CollectionError("query_row_count_mismatch")
    return sorted(parsed, key=lambda p: p["page"])


def collection_status(root: Path) -> dict:
    plan = load_plan(root)
    results = []
    for service, code, month in queries(plan):
        state, count, error = "not_collected", 0, None
        try:
            manifest = load_query(root, plan, service, code, month)
            parsed = verify_query(query_folder(root, service, code, month), manifest)
            state = manifest["status"]
            count = sum(p["rows"] for p in parsed)
            if state == "complete" and count == 0:
                state = "complete_zero"
            error = manifest.get("error")
        except CollectionError as exc:
            state, error = "invalid", str(exc)
        results.append({"service": service, "district": code, "month": month,
                        "status": state, "row_count": count, "error": error})
    completed = sum(q["status"] in {"complete", "complete_zero"} for q in results)
    return {"batch_id": plan["batch_id"], "query_count": len(results), "completed_queries": completed,
            "complete": completed == len(results), "queries": results,
            "counts_by_service": {s: sum(q["row_count"] for q in results if q["service"] == s)
                                  for s in plan["services"]}}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CollectionError("redirect_not_allowed")


def _open_request(request, *, timeout):
    return urllib.request.build_opener(_NoRedirect()).open(request, timeout=timeout)


def _secret_reflected(payload: bytes, key: str) -> bool:
    text = html.unescape(payload.decode("utf-8", errors="replace"))
    variants = {key, urllib.parse.unquote(key), urllib.parse.quote(key, safe=""),
                urllib.parse.quote_plus(key)}
    return any(v and v.casefold() in text.casefold() for v in variants)


def _recover_received(folder: Path, manifest: dict) -> bool:
    changed = False
    committed = {p["file"] for p in manifest["pages"]}
    for item in manifest["attempts"]:
        if item.get("status") != "received" or item["file"] in committed:
            continue
        path = safe_file(folder, item["file"])
        if not path.exists():
            item["status"] = "interrupted_write"
            changed = True
            continue
        if digest_file(path) != item["sha256"]:
            raise CollectionError("archive_integrity_failed")
        try:
            if item.get("http_status") != 200:
                raise CollectionError("interrupted_http_error_response")
            page = parse_page(path.read_bytes(), page=item["page"], per_page=manifest["per_page"],
                              code=manifest["district"], month=manifest["month"])
        except CollectionError as exc:
            item["status"], item["error"] = "error", str(exc)
        else:
            manifest["pages"].append(item | {"rows": len(page["rows"]), "total": page["total"]})
            item["status"] = "success"
        changed = True
    return changed


def _fetch_query(folder: Path, manifest: dict, key: str, *, opener, sleep, interval: float) -> None:
    if _recover_received(folder, manifest):
        write_json(folder / "manifest.json", manifest)
    parsed = verify_query(folder, manifest)
    if manifest["status"] == "complete":
        return
    if manifest["status"] == "inconsistent":
        raise CollectionError("inconsistent_query_use_new_batch")
    present = {p["page"] for p in parsed}
    total = parsed[0]["total"] if parsed else None
    number = 1
    while total is None or number <= max(1, math.ceil(total / manifest["per_page"])):
        if number in present:
            number += 1
            continue
        for retry in range(3):
            sleep(interval if retry == 0 else max(interval, 2 ** (retry - 1)))
            item = {"page": number, "retrieved_at_utc": utc_now()}
            try:
                query = {"LAWD_CD": manifest["district"], "DEAL_YMD": manifest["month"],
                         "pageNo": number, "numOfRows": manifest["per_page"], "serviceKey": key}
                request = urllib.request.Request(manifest["endpoint"] + "?" + urllib.parse.urlencode(query),
                                                 headers={"User-Agent": "jipdam-collection/1"})
                http_status = 200
                try:
                    with opener(request, timeout=20) as response:
                        payload = response.read(MAX_RESPONSE_BYTES + 1)
                except urllib.error.HTTPError as exc:
                    http_status = exc.code
                    payload = exc.read(MAX_RESPONSE_BYTES + 1)
                except (urllib.error.URLError, TimeoutError, OSError):
                    raise CollectionError("transient_transport_error") from None
                if len(payload) > MAX_RESPONSE_BYTES:
                    raise CollectionError("response_too_large")
                if _secret_reflected(payload, key):
                    raise CollectionError("credential_reflected_response_blocked")
                attempt = len(manifest["attempts"]) + 1
                item.update(file=f"page_{number:06d}_attempt_{attempt:06d}.xml", http_status=http_status,
                            sha256=hashlib.sha256(payload).hexdigest(), status="received")
                manifest["attempts"].append(item)
                manifest["status"] = "partial"
                # Journal the expected bytes before writing: a completed write can be recovered.
                write_json(folder / "manifest.json", manifest)
                with (folder / item["file"]).open("xb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                if http_status in {401, 403}:
                    raise CollectionError("authentication_error")
                if http_status == 429 or http_status >= 500:
                    raise CollectionError("transient_http_error")
                if http_status != 200:
                    raise CollectionError("http_error")
                page = parse_page(payload, page=number, per_page=manifest["per_page"],
                                  code=manifest["district"], month=manifest["month"])
                if total is not None and total != page["total"]:
                    raise CollectionError("pagination_total_changed")
                total = page["total"]
                item.update(status="success", rows=len(page["rows"]), total=total)
                manifest["pages"].append(dict(item))
                manifest.pop("error", None)
                write_json(folder / "manifest.json", manifest)
                break
            except CollectionError as exc:
                error = str(exc)
                item.update(status="error", error=error)
                if not manifest["attempts"] or manifest["attempts"][-1] is not item:
                    manifest["attempts"].append(item)
                manifest["error"] = error
                manifest["status"] = "inconsistent" if error in {
                    "pagination_total_changed", "pagination_metadata_mismatch", "page_row_count_mismatch",
                    "response_district_mismatch", "response_contract_month_mismatch"} else "failed"
                write_json(folder / "manifest.json", manifest)
                if not error.startswith("transient_") or retry == 2:
                    raise
        number += 1
    verify_query(folder, manifest, require_complete=True)
    manifest.update(status="complete", completed_at_utc=utc_now())
    manifest.pop("error", None)
    write_json(folder / "manifest.json", manifest)


def _reuse_query(root: Path, plan: dict, query: tuple, cache_dirs) -> bool:
    service, code, month = query
    destination = query_folder(root, *query)
    if (destination / "manifest.json").exists():
        return False
    for cache in cache_dirs:
        cache = Path(cache)
        if cache.resolve() == root.resolve():
            continue
        candidate = load_plan(cache)
        if service not in candidate["services"] or code not in candidate["districts"] or month not in candidate["months"]:
            continue
        manifest = load_query(cache, plan, service, code, month)
        if manifest["status"] not in {"complete", "partial", "failed"}:
            continue
        source = query_folder(cache, service, code, month)
        # Recover in memory; a donor archive is never rewritten by reuse.
        _recover_received(source, manifest)
        parsed = verify_query(source, manifest)
        if not parsed:
            continue
        required = max(1, math.ceil(parsed[0]["total"] / plan["per_page"]))
        if {p["page"] for p in parsed} == set(range(1, required + 1)):
            manifest["status"] = "complete"
            manifest.pop("error", None)
            verify_query(source, manifest, require_complete=True)
        destination.mkdir(parents=True, exist_ok=True)
        for entry in manifest["attempts"]:
            if "file" in entry:
                origin = safe_file(source, entry["file"])
                if entry.get("status") == "interrupted_write" and not origin.exists():
                    entry["expected_file"] = entry.pop("file")
                    entry["expected_sha256"] = entry.pop("sha256")
                    continue
                if not origin.is_file() or digest_file(origin) != entry["sha256"]:
                    raise CollectionError("archive_integrity_failed")
                with safe_file(destination, entry["file"]).open("xb") as stream:
                    with origin.open("rb") as raw:
                        shutil.copyfileobj(raw, stream)
        manifest = dict(manifest, reused_from_batch=candidate["batch_id"])
        write_json(destination / "manifest.json", manifest)
        return True
    return False


def fetch_collection(root: Path, credential_ids: dict, *, vault=None, opener=None,
                     sleep=time.sleep, interval: float = 1, limit: int | None = None,
                     cache_dirs=(), progress=None) -> dict:
    plan = load_plan(root)
    if not plan["record_url"]:
        raise CollectionError("github_collection_record_required")
    if not isinstance(interval, (int, float)) or isinstance(interval, bool) or not math.isfinite(interval) or interval < 0:
        raise CollectionError("invalid_request_interval")
    if limit is not None and (type(limit) is not int or limit < 1):
        raise CollectionError("invalid_query_limit")
    opener = opener or _open_request
    errors, blocked, keys = {}, set(), {}
    executed = 0
    # Exclusive batch lock avoids two writers charging the same incomplete query.
    lock_path = root / ".fetch.lock"
    try:
        lock = lock_path.open("x", encoding="utf-8")
    except FileExistsError:
        raise CollectionError("collection_in_use_remove_stale_lock_only_after_stopping_owner") from None
    try:
        lock.write(str(os.getpid()))
        lock.close()
        for query in queries(plan):
            _reuse_query(root, plan, query, cache_dirs)
            folder = query_folder(root, *query)
            manifest = load_query(root, plan, *query)
            if _recover_received(folder, manifest):
                parsed = verify_query(folder, manifest)
                if parsed and manifest["status"] != "inconsistent":
                    total = parsed[0]["total"]
                    required = max(1, math.ceil(total / plan["per_page"]))
                    if {p["page"] for p in parsed} == set(range(1, required + 1)):
                        manifest.update(status="complete", completed_at_utc=utc_now())
                        manifest.pop("error", None)
                write_json(folder / "manifest.json", manifest)
        before = collection_status(root)
        if any(q["status"] == "invalid" for q in before["queries"]):
            raise CollectionError("archive_integrity_failed")
        if before["complete"]:
            return before | {"new_queries": 0, "service_errors": {}}
        for query in queries(plan):
            service, code, month = query
            if service in blocked or (limit is not None and executed >= limit):
                continue
            folder = query_folder(root, *query)
            manifest = load_query(root, plan, *query)
            if manifest["status"] == "complete":
                continue
            try:
                if service not in keys:
                    credential_id = credential_ids.get(service)
                    if not credential_id:
                        raise CollectionError("credential_id_required")
                    if vault is None:
                        from .credential_vault import CredentialVault
                        vault = CredentialVault()
                    from .credential_vault import CredentialVaultError
                    try:
                        keys[service] = urllib.parse.unquote(vault.get_secret(credential_id).strip()).strip()
                    except CredentialVaultError:
                        raise CollectionError("credential_unavailable") from None
                    if not keys[service]:
                        raise CollectionError("credential_unavailable")
                    if any(c.isspace() for c in keys[service]):
                        raise CollectionError("credential_contains_internal_whitespace")
                executed += 1
                _fetch_query(folder, manifest, keys[service], opener=opener, sleep=sleep, interval=interval)
            except CollectionError as exc:
                errors[service] = str(exc)
                if str(exc) in {"authentication_error", "daily_quota_exceeded", "credential_unavailable",
                                "credential_id_required", "credential_reflected_response_blocked"}:
                    blocked.add(service)
            if progress:
                progress({"service": service, "district": code, "month": month,
                          "status": manifest["status"], "error": errors.get(service)})
        write_json(root / "fetch-result.json", {"service_errors": errors, "new_queries": executed})
        return collection_status(root) | {"new_queries": executed, "service_errors": errors}
    finally:
        keys.clear()
        lock_path.unlink(missing_ok=True)

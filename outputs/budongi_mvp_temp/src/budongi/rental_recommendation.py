"""Read-only, deterministic rental candidates. No model or provider calls."""
from __future__ import annotations

import calendar
import json
import math
import sqlite3
from datetime import date
from pathlib import Path

from .rental_storage import RENTAL_SCHEMA_VERSION

SEOUL_DISTRICTS = dict(zip(
    ("종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구", "성북구", "강북구", "도봉구", "노원구", "은평구", "서대문구", "마포구", "양천구", "강서구", "구로구", "금천구", "영등포구", "동작구", "관악구", "서초구", "강남구", "송파구", "강동구"),
    ("11110", "11140", "11170", "11200", "11215", "11230", "11260", "11290", "11305", "11320", "11350", "11380", "11410", "11440", "11470", "11500", "11530", "11545", "11560", "11590", "11620", "11650", "11680", "11710", "11740"),
))
FACILITY_KINDS = {"station", "supermarket", "park", "hospital"}
RENTAL_ALLOWED_TOOLS = frozenset({"recommend_rentals"})


class RentalInputError(ValueError):
    """Safe input error, without echoing supplied values."""


class RentalDataUnavailable(RuntimeError):
    """Data not ready; distinct from a successful empty result."""


class RentalInternalError(RuntimeError):
    """Safe database failure."""


def _text(value: object, label: str, maximum: int = 250) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise RentalInputError(f"{label}: 비어 있지 않은 문자열이 필요합니다.")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise RentalInputError(f"{label}: 문자 형식이 올바르지 않습니다.") from exc
    if any(ord(c) < 32 for c in value):
        raise RentalInputError(f"{label}: 제어 문자를 사용할 수 없습니다.")
    return value.strip()


def _number(value: object, label: str, *, positive: bool = False) -> float:
    if type(value) not in (int, float):
        raise RentalInputError(f"{label}: 유한한 숫자가 필요합니다.")
    try:
        result = float(value)
    except OverflowError as exc:
        raise RentalInputError(f"{label}: 허용 범위를 벗어났습니다.") from exc
    if not math.isfinite(result) or (positive and result <= 0):
        raise RentalInputError(f"{label}: 유한한 양수가 필요합니다.")
    return result


def _coordinates(body: dict) -> tuple[float, float]:
    latitude = _number(body.get("latitude"), "latitude")
    longitude = _number(body.get("longitude"), "longitude")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise RentalInputError("좌표 범위를 확인해 주세요.")
    return latitude, longitude


def validate_rental_request(arguments: object) -> dict:
    if not isinstance(arguments, dict):
        raise RentalInputError("추천 요청은 JSON 객체여야 합니다.")
    allowed = {"rental_type", "max_deposit_krw", "max_monthly_rent_krw", "districts",
               "area_min_sqm", "area_max_sqm", "workplace", "conditions", "limit"}
    if set(arguments) - allowed:
        raise RentalInputError("지원하지 않는 추천 입력 항목이 있습니다.")
    result = dict(arguments)
    if result.get("rental_type") not in ("jeonse", "wolse"):
        raise RentalInputError("rental_type은 jeonse 또는 wolse여야 합니다.")
    if result["rental_type"] == "jeonse":
        result.setdefault("max_monthly_rent_krw", 0)
    for key in ("max_deposit_krw", "max_monthly_rent_krw"):
        value = result.get(key)
        if type(value) is not int or not 0 <= value <= 9_223_372_036_854_775_807:
            raise RentalInputError(f"{key}: 0 이상의 원 정수를 입력해 주세요.")
    if result["rental_type"] == "jeonse" and result["max_monthly_rent_krw"] != 0:
        raise RentalInputError("전세의 월세 상한은 0이어야 합니다.")
    result.setdefault("limit", 5)
    if type(result["limit"]) is not int or not 1 <= result["limit"] <= 20:
        raise RentalInputError("limit은 1~20 정수여야 합니다.")
    for key in ("area_min_sqm", "area_max_sqm"):
        if key in result:
            result[key] = _number(result[key], key, positive=True)
    if result.get("area_min_sqm", 0) > result.get("area_max_sqm", math.inf):
        raise RentalInputError("면적 하한이 상한보다 큽니다.")
    if "districts" in result:
        districts = result["districts"]
        if not isinstance(districts, list) or not 1 <= len(districts) <= 25:
            raise RentalInputError("districts는 서울 자치구 이름/코드 목록이어야 합니다.")
        codes = []
        for district in districts:
            name = _text(district, "district", 30)
            code = SEOUL_DISTRICTS.get(name, name)
            if code not in SEOUL_DISTRICTS.values():
                raise RentalInputError("서울 자치구만 요청할 수 있습니다.")
            codes.append(code)
        result["districts"] = sorted(set(codes))
    if "workplace" in result:
        body = result["workplace"]
        if not isinstance(body, dict) or set(body) - {"latitude", "longitude", "verified", "source", "source_ref", "name", "place_id"}:
            raise RentalInputError("직장 위치는 확인한 좌표와 출처로 입력해 주세요.")
        if body.get("verified") is not True:
            raise RentalInputError("직장 위치를 먼저 확정해 주세요.")
        latitude, longitude = _coordinates(body)
        result["workplace"] = {"latitude": latitude, "longitude": longitude, "verified": True,
                               "source": _text(body.get("source"), "workplace source"),
                               "source_ref": _text(body.get("source_ref"), "workplace source_ref")}
        for key in ("name", "place_id"):
            if key in body:
                result["workplace"][key] = _text(body[key], f"workplace {key}", 100)
    conditions = result.get("conditions", [])
    if not isinstance(conditions, list) or len(conditions) > 20:
        raise RentalInputError("conditions는 최대 20개 조건 목록이어야 합니다.")
    checked, kinds = [], set()
    for condition in conditions:
        if not isinstance(condition, dict) or set(condition) != {"kind", "max_distance_m", "required"}:
            raise RentalInputError("조건에는 kind·max_distance_m·required를 입력해 주세요.")
        kind = _text(condition["kind"], "condition kind", 50)
        if kind in kinds:
            raise RentalInputError("같은 종류의 조건은 한 번만 요청할 수 있습니다.")
        kinds.add(kind)
        if type(condition["required"]) is not bool:
            raise RentalInputError("required는 true 또는 false여야 합니다.")
        if kind not in FACILITY_KINDS | {"workplace"} and condition["required"]:
            raise RentalInputError("지원하지 않는 시설을 필수 조건으로 사용할 수 없습니다.")
        if kind == "workplace" and "workplace" not in result:
            raise RentalInputError("직장 거리 조건에는 확정된 직장 위치가 필요합니다.")
        checked.append({"kind": kind, "max_distance_m": _number(condition["max_distance_m"], "max_distance_m", positive=True),
                        "required": condition["required"]})
    result["conditions"] = checked
    return result


def open_rental_reader(path: Path) -> sqlite3.Connection:
    path = Path(path).resolve()
    if not path.is_file():
        raise RentalDataUnavailable("전월세 스냅샷 DB가 준비되지 않았습니다.")
    try:
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return connection
    except sqlite3.Error as exc:
        raise RentalInternalError("전월세 DB를 열 수 없습니다.") from exc


def straight_distance_m(first: tuple[float, float], second: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*first, *second))
    value = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6_371_008.8 * 2 * math.asin(math.sqrt(min(1.0, max(0.0, value))))


def observation_period(end: date) -> tuple[str, str]:
    year = end.year - 1
    if year < 1:
        raise RentalDataUnavailable("스냅샷 기준일을 확인해 주세요.")
    start = date(year, end.month, min(end.day, calendar.monthrange(year, end.month)[1]))
    return start.isoformat(), end.isoformat()


def _date_known(value: object, cutoff: date) -> bool:
    try:
        start, _ = observation_period(cutoff)
        return (isinstance(value, str) and date.fromisoformat(value).isoformat() == value
                and date.fromisoformat(start) <= date.fromisoformat(value) <= cutoff)
    except ValueError:
        return False


def _dataset(row: dict, datasets: dict) -> dict:
    return datasets.get((row["source"], row["source_file_ref"]), {})


def _source(row: dict, datasets: dict) -> dict:
    dataset = _dataset(row, datasets)
    return {key: row.get(key) for key in ("source", "source_record_id", "source_file_ref", "source_content_sha256", "source_row_number", "ingested_at_utc")} | {
        "source_date": dataset.get("source_date"), "retrieved_at_utc": dataset.get("retrieved_at_utc")}


def _facility_condition(condition: dict, complex_row: dict, facilities: dict, coverage: dict, datasets: dict, cutoff: date) -> dict:
    result = dict(condition, status="unknown", distance_type="straight_line", distance_m=None, reason="시설 자료의 검수 범위·기준일이 부족합니다.")
    kind = condition["kind"]
    if kind not in FACILITY_KINDS:
        result["reason"] = "지원하지 않는 선호 시설입니다."
        return result
    coords = (complex_row["latitude"], complex_row["longitude"])
    if None in coords:
        result["reason"] = "단지 좌표가 확인되지 않았습니다."
        return result
    scope = coverage.get((kind, complex_row["sgg_cd"]))
    if not scope or scope["coverage_status"] != "complete":
        return result
    result["coverage_source"] = _source(scope, datasets) | {"checked_at_utc": scope["checked_at_utc"]}
    # A district catalog alone does not prove that a circle crossing its border is complete.
    area = json.loads(scope["raw_payload_json"]).get("coverage_area")
    if not isinstance(area, dict) or not _date_known(scope["checked_at_utc"][:10], cutoff):
        return result
    try:
        center = _coordinates(area)
        radius = _number(area.get("radius_m"), "coverage radius", positive=True)
    except RentalInputError:
        return result
    if straight_distance_m(center, coords) + condition["max_distance_m"] > radius + 1e-6:
        return result
    entries = facilities.get(kind, [])
    # Unknown/future basis dates inside the queried radius invalidate completeness.
    if any(not _date_known(_dataset(row, datasets).get("source_date"), cutoff) for row in entries):
        return result
    if not _date_known(_dataset(scope, datasets).get("source_date"), cutoff):
        return result
    nearest = min(entries, key=lambda row: (straight_distance_m(coords, (row["latitude"], row["longitude"])), row["facility_observation_id"]), default=None)
    distance = None if nearest is None else straight_distance_m(coords, (nearest["latitude"], nearest["longitude"]))
    result.update(status="met" if distance is not None and distance <= condition["max_distance_m"] + 1e-6 else "unmet",
                  distance_m=None if distance is None else round(distance, 3), reason="검수된 범위의 직선거리 조건을 비교했습니다.")
    if nearest:
        result["facility"] = {"id": nearest["facility_observation_id"], "name": nearest["name"], "source": _source(nearest, datasets)}
    return result


def recommend_rentals(connection: sqlite3.Connection, *, snapshot_id: str, arguments: object,
                      allow_synthetic: bool = False) -> dict:
    request = validate_rental_request(arguments)
    snapshot_id = _text(snapshot_id, "snapshot_id", 100)
    try:
        return _recommend(connection, snapshot_id, request, allow_synthetic)
    except sqlite3.Error as exc:
        raise RentalInternalError("전월세 스냅샷 조회에 실패했습니다.") from exc
    except (KeyError, TypeError, json.JSONDecodeError, ValueError) as exc:
        raise RentalDataUnavailable("스냅샷의 정규화·검수 정보를 확인해 주세요.") from exc


def _recommend(connection: sqlite3.Connection, snapshot_id: str, request: dict, allow_synthetic: bool) -> dict:
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='rental_schema'").fetchone() is None:
        raise RentalDataUnavailable("역사·자격증명 DB는 전월세 추천 DB로 사용할 수 없습니다.")
    schema = connection.execute("SELECT schema_version FROM rental_schema WHERE singleton=1").fetchone()
    if not schema or schema[0] != RENTAL_SCHEMA_VERSION:
        raise RentalDataUnavailable("지원되는 전월세 스키마가 아닙니다.")
    snapshot = connection.execute("SELECT * FROM rental_snapshots WHERE snapshot_id=?", (snapshot_id,)).fetchone()
    if not snapshot or snapshot["sealed"] != 1:
        raise RentalDataUnavailable("봉인된 전월세 스냅샷이 없습니다.")
    if snapshot["quality_status"] != "synthetic_only" or not allow_synthetic:
        raise RentalDataUnavailable("현재는 명시적으로 허용한 합성 데모만 지원합니다. 실데이터 검수는 아직 완료되지 않았습니다.")
    cutoff = date.fromisoformat(snapshot["snapshot_date"])
    start, end = observation_period(cutoff)
    manifest = json.loads(snapshot["source_manifest_json"])
    datasets = {(row["source"], file["path"]): row for row in manifest["datasets"] for file in row["files"]}
    where = "o.snapshot_id=? AND o.rental_type=? AND o.contract_date BETWEEN ? AND ?"
    params = [snapshot_id, request["rental_type"], start, end]
    codes = request.get("districts", sorted(SEOUL_DISTRICTS.values()))
    where += " AND c.sgg_cd IN (" + ",".join("?" for _ in codes) + ")"
    params.extend(codes)
    for field, operation in (("area_min_sqm", ">="), ("area_max_sqm", "<=")):
        if field in request:
            where += f" AND o.area_sqm {operation} ?"
            params.append(request[field])
    rows = [dict(row) for row in connection.execute(
        "SELECT o.*, c.complex_id, c.name AS complex_name, c.sgg_cd AS complex_sgg_cd, "
        "c.legal_dong AS complex_dong, c.jibun AS complex_jibun, c.latitude, c.longitude, "
        "c.source AS complex_source, c.source_record_id AS complex_source_record_id, "
        "c.source_file_ref AS complex_source_file_ref, c.source_content_sha256 AS complex_source_content_sha256, "
        "c.source_row_number AS complex_source_row_number, c.ingested_at_utc AS complex_ingested_at_utc, "
        "c.identity_evidence, m.match_basis, m.evidence AS match_evidence, m.reviewed_by, m.reviewed_at_utc "
        "FROM rental_observations o JOIN rental_observation_matches m "
        "ON m.snapshot_id=o.snapshot_id AND m.observation_id=o.observation_id AND m.review_status='confirmed' "
        "JOIN rental_complexes c ON c.snapshot_id=m.snapshot_id AND c.complex_id=m.complex_id WHERE " + where,
        params)]
    latest = {}
    for row in rows:
        if row["source_status"] == "cancelled":
            continue
        if row["source_status"] not in (None, "valid"):
            raise RentalDataUnavailable("취소·정정 상태의 정규화 또는 정정 연결 검수가 필요합니다.")
        old = latest.get(row["complex_id"])
        if old is None or (row["contract_date"], row["observation_id"]) > (old["contract_date"], old["observation_id"]):
            latest[row["complex_id"]] = row
    facilities = {}
    for row in connection.execute("SELECT * FROM rental_facilities WHERE snapshot_id=?", (snapshot_id,)):
        facilities.setdefault(row["category"], []).append(dict(row))
    coverage = {(row["category"], row["sgg_cd"]): dict(row) for row in connection.execute(
        "SELECT * FROM rental_facility_coverage WHERE snapshot_id=?", (snapshot_id,))}
    candidates = []
    workplace = request.get("workplace")
    for row in latest.values():
        if row["deposit_krw"] > request["max_deposit_krw"] or row["monthly_rent_krw"] > request["max_monthly_rent_krw"]:
            continue
        complex_row = {"latitude": row["latitude"], "longitude": row["longitude"], "sgg_cd": row["complex_sgg_cd"]}
        coords = None if row["latitude"] is None or row["longitude"] is None else _coordinates(complex_row)
        work_distance = None if workplace is None or coords is None else straight_distance_m(coords, _coordinates(workplace))
        checks = []
        for condition in request["conditions"]:
            if condition["kind"] == "workplace":
                status = "unknown" if work_distance is None else "met" if work_distance <= condition["max_distance_m"] + 1e-6 else "unmet"
                checks.append(dict(condition, status=status, distance_type="straight_line", distance_m=None if work_distance is None else round(work_distance, 3),
                                   reason="직장까지 직선거리입니다." if work_distance is not None else "단지 좌표가 확인되지 않았습니다."))
            else:
                checks.append(_facility_condition(condition, complex_row, facilities, coverage, datasets, cutoff))
        if any(check["required"] and check["status"] != "met" for check in checks):
            continue
        score = sum(not check["required"] and check["status"] == "met" for check in checks)
        candidates.append({"complex": {"id": row["complex_id"], "name": row["complex_name"], "sgg_cd": row["complex_sgg_cd"],
                                       "address": " ".join(filter(None, ("서울특별시", next(name for name, code in SEOUL_DISTRICTS.items() if code == row["complex_sgg_cd"]), row["complex_dong"], row["complex_jibun"]))),
                                       "source": _source({key: row["complex_" + key] for key in ("source", "source_record_id", "source_file_ref", "source_content_sha256", "source_row_number", "ingested_at_utc")}, datasets)},
                           "contract": {key: row[key] for key in ("observation_id", "contract_date", "rental_type", "area_sqm", "deposit_krw", "monthly_rent_krw", "source_status")},
                           "source": _source(row, datasets),
                           "matching": {key: row[key] for key in ("identity_evidence", "match_basis", "match_evidence", "reviewed_by", "reviewed_at_utc")},
                           "conditions": checks, "preference_met_count": score,
                           "ranking_basis": {"preference_met_count": score, "workplace_distance_m": None if work_distance is None else round(work_distance, 3),
                                             "contract_date": row["contract_date"], "complex_id": row["complex_id"]},
                           "unmet_preferences": [check["kind"] for check in checks if not check["required"] and check["status"] == "unmet"],
                           "unknown_preferences": [check["kind"] for check in checks if not check["required"] and check["status"] == "unknown"],
                           "workplace_distance": {"distance_m": None if work_distance is None else round(work_distance, 3), "distance_type": "straight_line", "source": workplace},
                           "_distance": work_distance,
                           "explanation": f"{row['contract_date']}의 같은 계약에서 보증금·월세 상한을 충족하며, 선호 조건 {score}개를 충족합니다."})
    candidates.sort(key=lambda row: (-row["preference_met_count"], row["_distance"] if workplace and row["_distance"] is not None else math.inf,
                                    -date.fromisoformat(row["contract"]["contract_date"]).toordinal(), row["complex"]["id"]))
    total = len(candidates)
    selected = candidates[:request["limit"]]
    for rank, candidate in enumerate(selected, 1):
        candidate.pop("_distance")
        candidate["rank"] = rank
    notices = ["합성 데이터 데모입니다. 실제 추천 품질을 검증한 결과가 아닙니다.",
               "실거래 관측에 근거한 단지 후보이며 현재 매물·계약 가능 가격은 확인할 수 없습니다.",
               "관리비·대출비용은 예산에 포함하지 않았습니다.", "모든 거리는 직선거리(m)이며 통근시간·도보거리가 아닙니다.",
               "확인되지 않은 개별 거래 ID·취소/정정 상태·출처 기준일은 추정하지 않습니다."]
    if total < request["limit"]:
        notices.append("조건을 자동 완화하지 않았으며 확인한 후보만 반환합니다.")
    if any(condition["kind"] not in FACILITY_KINDS | {"workplace"} for condition in request["conditions"]):
        notices.append("지원하지 않는 선호 시설은 미확인으로 표시합니다.")
    return {"status": "ok" if total else "no_match", "snapshot": {"id": snapshot_id, "date": end, "quality_status": snapshot["quality_status"]},
            "observation_period": {"from": start, "to": end}, "request": request, "row_count": len(selected), "eligible_count": total,
            "candidates": selected, "notices": notices, "explanation_mode": "deterministic",
            "excluded_costs": ["management_fee", "loan_costs"],
            "message": "조건에 맞는 단지 후보를 찾았습니다." if total else "예산·필수 조건을 만족하는 확인된 단지 후보가 없습니다."}


def execute_rental_tool(connection: sqlite3.Connection, *, snapshot_id: str, tool: str,
                        arguments: object, allow_synthetic: bool = False) -> dict:
    if tool not in RENTAL_ALLOWED_TOOLS:
        raise RentalInputError("허용되지 않은 전월세 Tool입니다.")
    return recommend_rentals(connection, snapshot_id=snapshot_id, arguments=arguments, allow_synthetic=allow_synthetic)

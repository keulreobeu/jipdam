"""Read-only reviewed rental serving from compatible canonical v2/v3 snapshots."""
from __future__ import annotations

import os
import json
import math
from bisect import insort
from collections import OrderedDict
from copy import deepcopy
from threading import Lock
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .rental_recommendation import (RentalDataUnavailable, RentalInputError, validate_rental_request,
                                    observation_period, straight_distance_m, evaluate_conditions, ranking_key,
                                    facility_condition, _date_known, SEOUL_DISTRICTS)
from .rental_review import file_sha256, load_review_package


APP_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANONICAL_DB = (
    APP_ROOT / "data" / "collection" / "molit-seoul-three-api-20261012-restored-20261013"
    / "canonical-v3-20261013" / "canonical.sqlite3"
)
DEFAULT_RENTAL_SERVING_DB = APP_ROOT / "data" / "rental" / "serving" / "canonical.sqlite3"
RENTAL_DATASET_ID = "15126474"
MAX_DETAIL_OBSERVATIONS = 100
SERVING_SCHEMA_VERSION = 2
CATALOG_VERSION = 2
_SPATIAL_CACHE: OrderedDict = OrderedDict()
_SPATIAL_CACHE_LOCK = Lock()
_MAX_SPATIAL_CACHE = 2048

DETAIL_FIELDS = (
    {"key": "observation_id", "label": "관측 ID", "unit": "id"},
    {"key": "complex_id", "label": "공식 연결 단지 ID", "unit": "id"},
    {"key": "sgg_cd", "label": "자치구 코드", "unit": "code"},
    {"key": "apartment_name", "label": "원천 단지명", "unit": "text"},
    {"key": "legal_dong", "label": "법정동", "unit": "text"},
    {"key": "jibun", "label": "지번", "unit": "text"},
    {"key": "contract_date", "label": "계약일", "unit": "date"},
    {"key": "kind", "label": "전월세 유형", "unit": "enum"},
    {"key": "deposit_krw", "label": "보증금", "unit": "KRW"},
    {"key": "monthly_rent_krw", "label": "월세", "unit": "KRW"},
    {"key": "area_sqm", "label": "전용 면적", "unit": "m²"},
    {"key": "floor", "label": "층", "unit": "floor"},
    {"key": "build_year", "label": "건축 연도", "unit": "year"},
    {"key": "source_record_id", "label": "원천 기록 ID", "unit": "id"},
    {"key": "source_effective_from", "label": "출처 효력 시작", "unit": "date"},
    {"key": "source_effective_to", "label": "출처 효력 종료", "unit": "date"},
    {"key": "source_id", "label": "출처 ID", "unit": "id"},
    {"key": "dataset_id", "label": "데이터셋 ID", "unit": "id"},
    {"key": "batch_id", "label": "배치 ID", "unit": "id"},
    {"key": "snapshot_date", "label": "스냅샷 기준일", "unit": "date"},
    {"key": "mapping_version", "label": "정규화 버전", "unit": "version"},
    {"key": "source_file_ref", "label": "원본 파일", "unit": "path"},
    {"key": "source_content_sha256", "label": "원본 SHA-256", "unit": "sha256"},
    {"key": "source_row_number", "label": "원본 행 번호", "unit": "row"},
)


def open_canonical_reader(path: Path | str = DEFAULT_CANONICAL_DB) -> sqlite3.Connection:
    """Open a canonical database without allowing writes."""
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise RentalDataUnavailable("실제 통합 DB가 준비되지 않았습니다.")
    try:
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        required = {"batches", "batch_observations", "observations", "sources", "complexes", "raw_items", "raw_files"}
        present = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if not required.issubset(present) or connection.execute('PRAGMA user_version').fetchone()[0] not in (2,3):
            connection.close()
            raise RentalDataUnavailable("지원하는 실제 통합 DB 스키마가 아닙니다.")
        return connection
    except sqlite3.Error as exc:
        raise RentalDataUnavailable("실제 통합 DB를 읽을 수 없습니다.") from exc


def prepare_canonical_rental_serving(
    source_path: Path | str = DEFAULT_CANONICAL_DB,
    destination_path: Path | str = DEFAULT_RENTAL_SERVING_DB,
    *, review_package: Path | None = None, allow_synthetic: bool = False,
) -> dict[str, Any]:
    """Build a compact, indexed projection; never write to the canonical source DB."""
    source_path = Path(source_path).expanduser().resolve()
    destination = Path(destination_path).expanduser().resolve()
    if source_path == destination or (destination.exists() and source_path.exists() and
                                      os.path.samefile(source_path, destination)):
        raise RentalDataUnavailable("canonical 원본과 serving 출력은 서로 다른 파일이어야 합니다.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    building = destination.with_name(destination.name + ".building-" + uuid4().hex)
    source = open_canonical_reader(source_path)
    target: sqlite3.Connection | None = None
    try:
        batch = _latest_complete_batch(source)
        if batch is None:
            raise RentalDataUnavailable("완료된 실제 데이터 배치가 없습니다.")
        source_hash = file_sha256(source_path)
        report_file = source_path.with_name('quality-report.json')
        if report_file.is_file():
            try:
                report = json.loads(report_file.read_text(encoding='utf-8'))
                source_version = source.execute('PRAGMA user_version').fetchone()[0]
                if report['schema_version'] != f'canonical_real_estate_v{source_version}' or report['files'][source_path.name] != source_hash:
                    raise ValueError('sealed source mismatch')
            except (ValueError, KeyError, TypeError) as exc:
                raise RentalDataUnavailable('canonical 봉인 보고서의 버전·해시가 일치하지 않습니다.') from exc
        review = (load_review_package(Path(review_package), source_hash, allow_synthetic=allow_synthetic)
                  if review_package else {'relations': [], 'coordinates': [], 'facilities': [], 'coverage': []})
        serving_date = review.get('manifest',{}).get('snapshot_date',batch['snapshot_date'])
        if date.fromisoformat(serving_date) < date.fromisoformat(batch['snapshot_date']):
            raise RentalDataUnavailable('통합 serving 기준일이 원본 배치 기준일보다 이전입니다.')
        target = sqlite3.connect(building)
        target.execute("PRAGMA journal_mode=DELETE")
        target.execute('PRAGMA user_version=2')
        target.executescript(
            """CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
               CREATE TABLE rental_observations(
                 observation_id TEXT PRIMARY KEY,complex_id TEXT,sgg_cd TEXT NOT NULL,
                 contract_date TEXT NOT NULL,apartment_name TEXT NOT NULL,legal_dong TEXT,jibun TEXT,
                 kind TEXT NOT NULL CHECK(kind IN ('jeonse','wolse')),
                 area_sqm REAL NOT NULL,deposit_krw INTEGER NOT NULL,monthly_rent_krw INTEGER NOT NULL,
                 floor INTEGER,build_year INTEGER,source_record_id TEXT,
                 source_effective_from TEXT,source_effective_to TEXT,mapping_version TEXT NOT NULL,
                 source_id TEXT NOT NULL,dataset_id TEXT NOT NULL,batch_id TEXT NOT NULL,
                 snapshot_date TEXT NOT NULL,source_file_ref TEXT NOT NULL,
                 source_content_sha256 TEXT NOT NULL,source_row_number INTEGER NOT NULL,
                 source_status TEXT NOT NULL DEFAULT 'unreviewed');
               CREATE TABLE complexes(
                 complex_id TEXT PRIMARY KEY,sgg_cd TEXT NOT NULL,identifier_namespace TEXT NOT NULL,
                 source_complex_id TEXT NOT NULL,identity_basis TEXT NOT NULL,
                 latitude REAL,longitude REAL,coordinate_review_json TEXT);
               CREATE TABLE reviewed_relations(observation_id TEXT PRIMARY KEY,complex_id TEXT NOT NULL,
                 provenance_json TEXT NOT NULL);
               CREATE TABLE field_catalog(key TEXT PRIMARY KEY,definition_json TEXT NOT NULL);
               CREATE TABLE facilities(id INTEGER PRIMARY KEY,facility_id TEXT UNIQUE NOT NULL,
                 category TEXT NOT NULL,name TEXT,latitude REAL NOT NULL,longitude REAL NOT NULL,
                 provenance_json TEXT NOT NULL);
               CREATE VIRTUAL TABLE facility_rtree USING rtree(id,min_lat,max_lat,min_lon,max_lon);
               CREATE TABLE coverage(category TEXT NOT NULL,sgg_cd TEXT NOT NULL,
                 provenance_json TEXT NOT NULL,PRIMARY KEY(category,sgg_cd));"""
        )
        target.execute("BEGIN")
        cursor = source.execute(
            """SELECT o.observation_id,o.complex_id,o.sgg_cd,o.contract_date,o.apartment_name,
                      o.legal_dong,o.jibun,o.kind,o.area_sqm,o.deposit_krw,o.monthly_rent_krw,
                      o.floor,o.build_year,o.source_record_id,o.source_effective_from,
                      o.source_effective_to,o.mapping_version,s.source_id,s.dataset_id,
                      b.batch_id,b.snapshot_date,rf.file_ref,rf.sha256,ri.row_number
                 FROM batch_observations AS bo
                 JOIN observations AS o ON o.observation_id=bo.observation_id
                 JOIN sources AS s ON s.source_id=o.source_id
                 JOIN batches AS b ON b.batch_id=bo.batch_id
                 JOIN raw_items AS ri ON ri.raw_item_id=o.raw_item_id
                 JOIN raw_files AS rf ON rf.file_id=ri.file_id
                WHERE bo.batch_id=? AND s.dataset_id=? AND o.kind IN ('jeonse','wolse')
                ORDER BY o.observation_id""",
            (batch["batch_id"], RENTAL_DATASET_ID),
        )
        insert = "INSERT INTO rental_observations VALUES (" + ",".join("?" for _ in range(25)) + ")"
        row_count = 0
        while rows := cursor.fetchmany(5000):
            # A canonical entity ID alone is not review evidence. Never promote it.
            target.executemany(insert, [tuple([row[0], None, *tuple(row)[2:], 'unreviewed']) for row in rows])
            row_count += len(rows)
        expected_count = source.execute('SELECT COUNT(*) FROM batch_observations bo JOIN observations o ON o.observation_id=bo.observation_id '
                                        'JOIN sources s ON s.source_id=o.source_id WHERE bo.batch_id=? AND s.dataset_id=? '
                                        "AND o.kind IN ('jeonse','wolse')", (batch['batch_id'], RENTAL_DATASET_ID)).fetchone()[0]
        if row_count != expected_count:
            raise RentalDataUnavailable('원본 관측과 raw 파일·행 계보 조인 건수가 다릅니다.')
        for relation in review['relations']:
            if relation['review_status'] != 'confirmed':
                continue
            observation = target.execute('SELECT sgg_cd FROM rental_observations WHERE observation_id=?',
                                         (relation['observation_id'],)).fetchone()
            complex_row = source.execute('SELECT complex_id,sgg_cd,identifier_namespace,source_complex_id,identity_basis '
                                         'FROM complexes WHERE complex_id=?', (relation['complex_id'],)).fetchone()
            if (not observation or not complex_row or observation[0] != complex_row['sgg_cd'] or
                    observation[0] not in SEOUL_DISTRICTS.values()):
                raise RentalDataUnavailable('검수 관계의 원본 관측·단지·지역을 대사하지 못했습니다.')
            target.execute('INSERT INTO reviewed_relations VALUES (?,?,?)',
                           (relation['observation_id'], relation['complex_id'], json.dumps(relation, ensure_ascii=False)))
            target.execute('UPDATE rental_observations SET complex_id=?,source_status=? WHERE observation_id=?',
                           (relation['complex_id'], relation['source_status'], relation['observation_id']))
            target.execute('INSERT OR IGNORE INTO complexes VALUES (?,?,?,?,?,NULL,NULL,NULL)', tuple(complex_row))
        for coordinate in review['coordinates']:
            if coordinate['review_status'] != 'confirmed':
                continue
            existing = target.execute('SELECT coordinate_review_json FROM complexes WHERE complex_id=?',
                                      (coordinate['complex_id'],)).fetchone()
            if not existing or existing[0] is not None:
                raise RentalDataUnavailable('좌표는 추천 자격이 있는 단지마다 한 번만 등록할 수 있습니다.')
            target.execute('UPDATE complexes SET latitude=?,longitude=?,coordinate_review_json=? WHERE complex_id=?',
                           (coordinate['latitude'], coordinate['longitude'], json.dumps(coordinate, ensure_ascii=False), coordinate['complex_id']))
        for facility in review['facilities']:
            if facility['review_status'] != 'confirmed':
                continue
            cursor = target.execute('INSERT INTO facilities(facility_id,category,name,latitude,longitude,provenance_json) '
                                    'VALUES (?,?,?,?,?,?)', (facility['facility_id'], facility['category'], facility.get('name'),
                                    facility['latitude'], facility['longitude'], json.dumps(facility, ensure_ascii=False)))
            target.execute('INSERT INTO facility_rtree VALUES (?,?,?,?,?)',
                           (cursor.lastrowid, facility['latitude'], facility['latitude'], facility['longitude'], facility['longitude']))
        for coverage in review['coverage']:
            if coverage['review_status'] == 'confirmed':
                target.execute('INSERT INTO coverage VALUES (?,?,?)',
                               (coverage['category'], coverage['sgg_cd'], json.dumps(coverage, ensure_ascii=False)))
        catalog = field_catalog()
        target.executemany('INSERT INTO field_catalog VALUES (?,?)',
                           [(field['key'], json.dumps(field, ensure_ascii=False)) for field in catalog])
        target.executescript(
            """CREATE INDEX rental_search ON rental_observations
                   (kind,sgg_cd,contract_date DESC,area_sqm,complex_id,observation_id,source_status,batch_id,dataset_id);
               CREATE INDEX rental_complex_latest ON rental_observations
                   (complex_id,contract_date DESC,observation_id DESC) WHERE complex_id IS NOT NULL;
               CREATE INDEX rental_kind_date ON rental_observations(kind,contract_date DESC);"""
        )
        metadata = {
            "schema_version": str(SERVING_SCHEMA_VERSION),
            "source_schema_version": str(source.execute('PRAGMA user_version').fetchone()[0]),
            "source_dataset_id": RENTAL_DATASET_ID,
            "source_batch_id": batch["batch_id"],
            "snapshot_date": serving_date,
            "source_snapshot_date": batch['snapshot_date'],
            "source_observations": str(row_count),
            "built_at_utc": datetime.now(timezone.utc).isoformat(),
            "catalog_version": str(CATALOG_VERSION), "source_db_sha256": source_hash,
            "review_manifest_sha256": review.get('manifest_sha256', ''),
            "quality_status": review.get('manifest', {}).get('quality_status', 'source_unverified'),
            "unsupported_source_fields": json.dumps(sorted({row[1] for row in source.execute('PRAGMA table_info(observations)')}
                                                           - {field['key'] for field in catalog}), ensure_ascii=False),
        }
        metadata['by_kind'] = json.dumps({row[0]: {'observations': row[1], 'linked': row[2]} for row in target.execute(
            'SELECT kind,COUNT(*),SUM(complex_id IS NOT NULL) FROM rental_observations GROUP BY kind')})
        metadata['coordinates_available'] = str(bool(target.execute('SELECT 1 FROM complexes WHERE latitude IS NOT NULL LIMIT 1').fetchone()))
        metadata['facility_data_available'] = str(bool(target.execute('SELECT 1 FROM facilities LIMIT 1').fetchone()))
        metadata['coverage_available'] = str(bool(target.execute('SELECT 1 FROM coverage LIMIT 1').fetchone()))
        target.executemany("INSERT INTO metadata VALUES (?,?)", metadata.items())
        target.execute("ANALYZE")
        target.commit()
        if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RentalDataUnavailable('serving 무결성 검사가 실패했습니다.')
        if target.execute('SELECT COUNT(*) FROM rental_observations').fetchone()[0] != row_count:
            raise RentalDataUnavailable('원본 관측 수 대사가 실패했습니다.')
        if target.execute("SELECT 1 FROM rental_observations WHERE length(source_content_sha256)!=64 OR source_file_ref='' OR source_row_number<1 LIMIT 1").fetchone():
            raise RentalDataUnavailable('원본 계보가 누락되었습니다.')
        if file_sha256(source_path) != source_hash:
            raise RentalDataUnavailable('재생성 중 canonical 원본이 변경되었습니다.')
        target.close()
        target = None
        os.replace(building, destination)
        return {"status": "ready", "database": str(destination), "source_batch_id": batch["batch_id"],
                "snapshot_date": serving_date, "observations": row_count,
                "schema_version": SERVING_SCHEMA_VERSION}
    except Exception:
        if target is not None:
            target.close()
        try:
            building.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    finally:
        source.close()


def open_rental_serving_reader(path: Path | str = DEFAULT_RENTAL_SERVING_DB, *, allow_synthetic: bool = False) -> sqlite3.Connection:
    """Open the compact projection read-only and reject stale/unknown schemas."""
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise RentalDataUnavailable("실제 전월세 serving DB가 없습니다. 먼저 prepare 명령을 실행해 주세요.")
    connection = None
    try:
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        metadata = dict(connection.execute("SELECT key,value FROM metadata"))
        required_metadata = {'schema_version','catalog_version','source_schema_version','source_snapshot_date','source_db_sha256','review_manifest_sha256','quality_status',
                             'by_kind','coordinates_available','facility_data_available','coverage_available',
                             'source_batch_id','snapshot_date','source_dataset_id','unsupported_source_fields'}
        if not required_metadata.issubset(metadata):
            connection.close()
            raise RentalDataUnavailable('serving 메타데이터가 누락되었습니다. 재생성해 주세요.')
        if metadata.get("schema_version") != str(SERVING_SCHEMA_VERSION):
            connection.close()
            raise RentalDataUnavailable("전월세 serving DB 버전이 지원되지 않습니다.")
        if metadata.get('catalog_version') != str(CATALOG_VERSION):
            connection.close()
            raise RentalDataUnavailable('필드 카탈로그 버전이 지원되지 않습니다.')
        if metadata.get('quality_status') == 'synthetic_only' and not allow_synthetic:
            connection.close()
            raise RentalDataUnavailable('합성 serving DB는 명시적으로 허용해야 합니다.')
        return connection
    except sqlite3.Error as exc:
        if connection is not None:
            connection.close()
        raise RentalDataUnavailable("실제 전월세 serving DB를 읽을 수 없습니다.") from exc


def _latest_complete_batch(connection: sqlite3.Connection) -> sqlite3.Row | None:
    return connection.execute(
        """SELECT b.batch_id,b.snapshot_date
             FROM batches AS b
             LEFT JOIN batch_observations AS bo ON bo.batch_id=b.batch_id
            WHERE b.complete=1
            GROUP BY b.batch_id,b.snapshot_date
            ORDER BY b.snapshot_date DESC,COUNT(bo.observation_id) DESC,b.batch_id DESC
            LIMIT 1"""
    ).fetchone()


def canonical_rental_status(connection: sqlite3.Connection) -> dict[str, Any]:
    """Report data readiness without promoting unreviewed matching candidates."""
    metadata = dict(connection.execute("SELECT key,value FROM metadata"))
    # Counts are reconciled before atomic publication. Read-only serving has no writes.
    by_kind = json.loads(metadata['by_kind'])
    total = sum(value["observations"] for value in by_kind.values())
    linked = sum(value["linked"] for value in by_kind.values())
    if not metadata.get("source_batch_id"):
        state = "data_not_ready"
        reason = "완료된 실제 데이터 배치가 없습니다."
    elif total == 0 or linked == 0:
        state = "data_not_ready"
        reason = "확정된 단지와 연결된 전월세 관측이 아직 없습니다. 미확정 후보는 추천에서 제외합니다."
    else:
        state = "ready"
        reason = None
    return {
        "status": state,
        "reason": reason,
        "dataset_id": metadata.get("source_dataset_id"),
        "batch_id": metadata.get("source_batch_id"),
        "snapshot_date": metadata.get("snapshot_date"),
        "source_snapshot_date": metadata.get('source_snapshot_date'),
        "observations": total,
        "confirmed_complex_observations": linked,
        "by_kind": by_kind,
        "coordinates_available": metadata['coordinates_available'] == 'True',
        "facility_data_available": metadata['facility_data_available'] == 'True',
        "matching_policy": "reviewed_relation_only",
        "schema_version": int(metadata['schema_version']), "catalog_version": int(metadata['catalog_version']),
        "source_schema_version": int(metadata['source_schema_version']),
        "quality_status": metadata['quality_status'], "serving_version": metadata['source_db_sha256'] + ':' + metadata['review_manifest_sha256'],
        "coverage_available": metadata['coverage_available'] == 'True',
    }


def field_catalog() -> list[dict]:
    """Registered serving fields; changes require a catalog/schema version and rebuild."""
    numeric = {'deposit_krw', 'monthly_rent_krw', 'floor', 'build_year', 'source_row_number'}
    return [{**field, 'type': 'integer' if field['key'] in numeric else 'number' if field['key'] == 'area_sqm' else 'string',
             'section': 'provenance' if field['key'].startswith('source_') or field['key'] in ('batch_id', 'snapshot_date', 'dataset_id', 'mapping_version') else 'transaction',
             'source': 'review-package/canonical-entity' if field['key']=='complex_id' else 'review-package' if field['key']=='source_status' else 'canonical-normalized',
             'validity': 'reviewed_at_utc/source_date; snapshot_date' if field['key'] in ('complex_id','source_status') else 'source_effective_from/source_effective_to; snapshot_date'}
            for field in (*DETAIL_FIELDS, {'key': 'source_status', 'label': '취소·정정 검수 상태', 'unit': 'enum'})]


def _catalog(connection) -> list[dict]:
    return [json.loads(row[0]) for row in connection.execute('SELECT definition_json FROM field_catalog ORDER BY rowid')]


def _nearby_facilities(connection, coords, kind, radius, cache=None, *, summary=False):
    entries = []
    nearest = None
    dates_complete = True
    if coords is None or None in coords:
        return entries
    lat, lon = coords
    angular = min(math.pi, (radius + 0.01) / 6_371_008.8)
    lat_delta = math.degrees(angular)
    lon_delta = 180 if abs(lat)+lat_delta >= 90 else math.degrees(math.asin(min(1, math.sin(angular)/math.cos(math.radians(lat)))))
    low_lon, high_lon = (lon-lon_delta, lon+lon_delta) if -180 <= lon-lon_delta and lon+lon_delta <= 180 else (-180,180)
    rows = connection.execute('SELECT f.id FROM facility_rtree r JOIN facilities f ON f.id=r.id '
                              'WHERE r.min_lat<=? AND r.max_lat>=? AND r.min_lon<=? AND r.max_lon>=? AND f.category=?',
                              (min(90,lat+lat_delta), max(-90,lat-lat_delta), high_lon, low_lon, kind))
    if cache is None:
        catalog = {row['id']: dict(row) for row in connection.execute('SELECT * FROM facilities')}
    else:
        catalog = cache['facilities']
    for found in rows:
        row = catalog[found[0]]
        distance = straight_distance_m(coords, (row['latitude'],row['longitude']))
        if distance > radius + 1e-6: continue
        if summary:
            dates_complete = dates_complete and row['date_valid']
            pair = (distance,row['facility_id'],row)
            if nearest is None or pair[:2] < nearest[:2]: nearest = pair
        else:
            evidence = row.get('source') or json.loads(row['provenance_json'])
            entries.append({'id':row['facility_id'],'facility_id':row['facility_id'],'category':row['category'],
                            'name':row['name'],'latitude':row['latitude'],'longitude':row['longitude'],
                            'source':evidence,'source_date':evidence['source_date'],'_distance_m':distance,
                            'distance_m':round(distance,3),'distance_type':'straight_line'})
    if summary:
        if nearest:
            distance, _, row = nearest
            entries = [{'id':row['facility_id'],'name':row['name'],'latitude':row['latitude'],'longitude':row['longitude'],
                        'source':row['source'],'source_date':row['source_date'],'_distance_m':distance}]
        return entries, dates_complete
    return entries


def _candidate_facility_summaries(connection, coords, conditions, cache):
    """One RTree range scan for all requested categories, then exact per-radius checks."""
    radii = {item['kind']:item['max_distance_m'] for item in conditions if item['kind'] in {'station','supermarket','park','hospital'}}
    # Cache only immutable, DB-backed spatial evidence; decisions/ranks still run on every request.
    # Source+review hash, cutoff, coordinates and all radii prevent cross-version reuse.
    cache_key = (cache['version'], coords, tuple(sorted(radii.items())))
    with _SPATIAL_CACHE_LOCK:
        existing = _SPATIAL_CACHE.get(cache_key)
        if existing is not None:
            _SPATIAL_CACHE.move_to_end(cache_key)
            return existing
    nearest = {kind:None for kind in radii}
    dates = {kind:True for kind in radii}
    if coords is not None and None not in coords and radii:
        lat, lon = coords
        angular = min(math.pi, (max(radii.values())+0.01)/6_371_008.8)
        delta = math.degrees(angular)
        lon_delta = 180 if abs(lat)+delta>=90 else math.degrees(math.asin(min(1,math.sin(angular)/math.cos(math.radians(lat)))))
        low, high = (lon-lon_delta,lon+lon_delta) if -180<=lon-lon_delta and lon+lon_delta<=180 else (-180,180)
        rows = connection.execute('SELECT id FROM facility_rtree WHERE min_lat<=? AND max_lat>=? AND min_lon<=? AND max_lon>=?',
                                  (min(90,lat+delta),max(-90,lat-delta),high,low))
        for found in rows:
            row = cache['facilities'][found[0]]
            kind = row['category']
            if kind not in radii: continue
            distance = straight_distance_m(coords,(row['latitude'],row['longitude']))
            if distance > radii[kind]+1e-6: continue
            dates[kind] = dates[kind] and row['date_valid']
            pair = (distance,row['facility_id'],row)
            if nearest[kind] is None or pair[:2]<nearest[kind][:2]: nearest[kind]=pair
    summaries = {}
    for kind,pair in nearest.items():
        if pair is None and coords is not None and kind in cache.get('available_kinds', set()):
            # Preserve the actual nearest current facility even when it lies outside
            # the requested radius. Completeness still uses only the requested circle.
            radius = min(20_020_000.0, max(100.0, radii[kind]*2))
            while True:
                extended = [row for row in _nearby_facilities(connection, coords, kind, radius, cache)
                            if _date_known(row['source_date'],cache['cutoff'])]
                if extended:
                    nearest_row = min(extended,key=lambda row:(row['_distance_m'],row['facility_id']))
                    pair = (nearest_row['_distance_m'],nearest_row['facility_id'],nearest_row)
                    break
                if radius >= 20_020_000: break
                radius = min(20_020_000.0,radius*2)
        entries = []
        if pair:
            distance, _, row = pair
            entries = [{'id':row['facility_id'],'name':row['name'],'latitude':row['latitude'],'longitude':row['longitude'],
                        'source':row['source'],'source_date':row['source_date'],'_distance_m':distance}]
        summaries[kind] = (entries,dates[kind])
    with _SPATIAL_CACHE_LOCK:
        _SPATIAL_CACHE[cache_key] = summaries
        while len(_SPATIAL_CACHE) > _MAX_SPATIAL_CACHE:
            _SPATIAL_CACHE.popitem(last=False)
    return summaries


def _facility_lookup(connection, condition, complex_row, cutoff, cache=None):
    key = (condition['kind'], complex_row['sgg_cd'])
    if cache is not None:
        scope = cache['coverage'].get(key)
    else:
        raw_scope = connection.execute('SELECT provenance_json FROM coverage WHERE category=? AND sgg_cd=?',key).fetchone()
        scope = json.loads(raw_scope[0]) if raw_scope else None
        if scope: scope = {**scope,'source':scope}
    coords = (complex_row['latitude'], complex_row['longitude'])
    preliminary = facility_condition(condition, coords, scope, [], cutoff)
    if cache is not None:
        entries, dates_complete = cache['nearby'].get(condition['kind'], ([],True))
    else:
        if preliminary['status'] == 'unknown': return preliminary
        entries = _nearby_facilities(connection, coords, condition['kind'], condition['max_distance_m'])
        dates_complete = True
    return facility_condition(condition, coords, scope, entries, cutoff, dates_complete=dates_complete)


def recommendation_query(request, state):
    start, end = observation_period(date.fromisoformat(state['snapshot_date']))
    clauses = ['batch_id=?', 'dataset_id=?', 'kind=?', 'complex_id IS NOT NULL', 'source_status!=?', 'contract_date BETWEEN ? AND ?']
    values = [state['batch_id'], RENTAL_DATASET_ID, request['rental_type'], 'cancelled', start, end]
    districts = request.get('districts', sorted(SEOUL_DISTRICTS.values()))
    clauses.append('sgg_cd IN (' + ','.join('?' for _ in districts) + ')')
    values.extend(districts)
    for field, operator in [('area_min_sqm', '>='), ('area_max_sqm', '<=')]:
        if field in request:
            clauses.append('area_sqm' + operator + '?')
            values.append(request[field])
    where = ' AND '.join(clauses)
    # Rank narrow observation IDs first; materializing provenance for every historical
    # contract makes the window sort much larger than the actual candidate set.
    sql = ('WITH ranked AS (SELECT observation_id,complex_id,ROW_NUMBER() OVER (PARTITION BY complex_id '
           'ORDER BY contract_date DESC,observation_id DESC) AS candidate_rank FROM rental_observations o WHERE ' + where + ') '
           'SELECT o.*,c.latitude,c.longitude,c.coordinate_review_json,m.provenance_json AS matching_json FROM ranked r '
           'JOIN rental_observations o ON o.observation_id=r.observation_id '
           'JOIN complexes c ON c.complex_id=r.complex_id JOIN reviewed_relations m ON m.observation_id=r.observation_id '
           'WHERE candidate_rank=1 AND o.deposit_krw<=? AND o.monthly_rent_krw<=?')
    return sql, [*values, request['max_deposit_krw'], request['max_monthly_rent_krw']], (start, end), where, values


def recommend_canonical_rentals(connection: sqlite3.Connection, arguments: object,
                                state: dict[str, Any] | None = None) -> dict[str, Any]:
    request = validate_rental_request(arguments)
    state = state or canonical_rental_status(connection)
    unknown = [{**item, 'status': 'unknown', 'reason': '검수된 위치·시설 자료가 없습니다.'} for item in request['conditions']]
    base = {**state, 'results': [], 'count': 0, 'conditions': unknown, 'request': request,
            'notices': ['과거 실거래 기반 단지 후보입니다. 현재 매물·계약 가능 가격은 확인되지 않았습니다.',
                        '관리비·대출비용 미포함. 거리는 직선거리이며 도보거리·통근시간이 아닙니다.']}
    if state['quality_status'] == 'synthetic_only':
        base['notices'].insert(0, '합성 검증 데이터입니다. 실제 추천 결과가 아닙니다.')
    if state['status'] != 'ready':
        return base
    sql, params, period, where, values = recommendation_query(request, state)
    if connection.execute('SELECT 1 FROM rental_observations WHERE ' + where + ' AND source_status!=? LIMIT 1',
                          [*values, 'valid']).fetchone():
        return {**base, 'status': 'data_not_ready', 'reason': '취소·정정 상태의 추가 검수가 필요합니다.'}
    cache = {'coverage':{},'facilities':{},'version':(state['serving_version'],state['snapshot_date'],state['catalog_version']),
             'cutoff':date.fromisoformat(state['snapshot_date']), 'available_kinds':set()}
    for row in connection.execute('SELECT * FROM coverage'):
        scope = json.loads(row['provenance_json'])
        cache['coverage'][(row['category'],row['sgg_cd'])] = {**scope,'source':scope}
    if any(condition['kind'] != 'workplace' for condition in request['conditions']):
        for row in connection.execute('SELECT * FROM facilities'):
            evidence = json.loads(row['provenance_json'])
            cache['facilities'][row['id']] = {**dict(row),'source':evidence,'source_date':evidence['source_date'],
                                            'date_valid':_date_known(evidence['source_date'],date.fromisoformat(state['snapshot_date']))}
            if cache['facilities'][row['id']]['date_valid']:
                cache['available_kinds'].add(row['category'])
    selected = []
    total = required_unknown = rejected_known = 0
    cursor = connection.execute(sql, params)
    while rows := cursor.fetchmany(200):
        for row in rows:
            coords = None if row['latitude'] is None or row['longitude'] is None else (row['latitude'], row['longitude'])
            cache['nearby'] = _candidate_facility_summaries(connection, coords, request['conditions'], cache)
            checks, score, distance = evaluate_conditions(request, coords,
                lambda condition: _facility_lookup(connection, condition, row, date.fromisoformat(state['snapshot_date']), cache))
            failed = [check for check in checks if check['required'] and check['status'] != 'met']
            if failed:
                if any(check['status'] == 'unmet' for check in failed):
                    rejected_known += 1
                else:
                    required_unknown += 1
                continue
            total += 1
            item = {key: row[key] for key in ('complex_id', 'sgg_cd', 'legal_dong', 'jibun', 'observation_id', 'contract_date',
                                             'area_sqm', 'deposit_krw', 'monthly_rent_krw', 'floor', 'build_year')}
            item.update(name=row['apartment_name'], rental_type=row['kind'],
                        coordinates=None if coords is None else {'latitude': coords[0], 'longitude': coords[1],
                                                                'review': json.loads(row['coordinate_review_json'])},
                        matching=json.loads(row['matching_json']), conditions=checks, preference_met_count=score,
                        workplace_distance_m=None if distance is None else round(distance, 3),
                        provenance={key: row[key] for key in ('source_id', 'dataset_id', 'batch_id', 'snapshot_date', 'mapping_version',
                                                             'source_file_ref', 'source_content_sha256', 'source_row_number')})
            item['needs'] = [
                {'kind': 'rental_type', 'label': '전월세 유형', 'status': 'met', 'actual': row['kind'], 'expected': request['rental_type']},
                {'kind': 'budget', 'label': '예산', 'status': 'met',
                 'actual': {'deposit_krw': row['deposit_krw'], 'monthly_rent_krw': row['monthly_rent_krw']},
                 'expected': {'max_deposit_krw': request['max_deposit_krw'], 'max_monthly_rent_krw': request['max_monthly_rent_krw']}},
                {'kind': 'district', 'label': '지역', 'status': 'met', 'actual': row['sgg_cd'], 'expected': request.get('districts', '서울 전체')},
                {'kind': 'area', 'label': '면적', 'status': 'met', 'actual': row['area_sqm'],
                 'expected': {key: request[key] for key in ('area_min_sqm', 'area_max_sqm') if key in request}},
                *checks]
            for need in item['needs']:
                need.setdefault('reason', 'DB 대표 계약의 실제 값과 요청 기준을 비교했습니다.')
                need.setdefault('source', item['provenance'])
            item['ranking_basis'] = {'preference_met_count': score, 'workplace_distance_m': item['workplace_distance_m'],
                                     'contract_date': row['contract_date'], 'complex_id': row['complex_id']}
            key = ranking_key(score, distance, row['contract_date'], row['complex_id'])
            insort(selected, (key, item))
            if len(selected) > request['limit']:
                selected.pop()
    results = [deepcopy(item) for _, item in selected]
    for rank, item in enumerate(results, 1):
        item['rank'] = rank
    status = 'ok' if results else 'data_not_ready' if required_unknown else 'no_match'
    return {**base, 'status': status, 'results': results, 'count': len(results), 'eligible_count': total,
            'conditions': [] if results else unknown if status == 'data_not_ready' else [],
            'reason': None if results else '필수 조건 판정에 필요한 검수 자료가 부족합니다.' if required_unknown else '요청 조건을 만족하는 확정 후보가 없습니다.',
            'required_unknown_count': required_unknown, 'known_rejected_count': rejected_known,
            'period': {'from': period[0], 'to': period[1]}}


def canonical_complex_detail(connection: sqlite3.Connection, complex_id: str,
                             state: dict[str, Any] | None = None, offset: int = 0) -> dict[str, Any]:
    if not isinstance(complex_id, str) or not complex_id or len(complex_id) > 200:
        raise RentalInputError('단지 ID가 올바르지 않습니다.')
    if type(offset) is not int or not 0 <= offset <= 9_223_372_036_854_775_807 or offset % MAX_DETAIL_OBSERVATIONS:
        raise RentalInputError('상세 페이지 번호가 올바르지 않습니다.')
    state = state or canonical_rental_status(connection)
    fields = _catalog(connection)
    complex_row = connection.execute('SELECT * FROM complexes WHERE complex_id=?', (complex_id,)).fetchone()
    if complex_row is None:
        return {**state, 'status': 'not_found', 'complex': None, 'observations': [], 'fields': fields}
    total = connection.execute('SELECT COUNT(*) FROM rental_observations WHERE complex_id=?', (complex_id,)).fetchone()[0]
    rows = connection.execute('SELECT * FROM rental_observations WHERE complex_id=? '
                              'ORDER BY contract_date DESC,observation_id DESC LIMIT ? OFFSET ?',
                              (complex_id, MAX_DETAIL_OBSERVATIONS, offset)).fetchall()
    first = connection.execute('SELECT apartment_name,legal_dong,jibun FROM rental_observations WHERE complex_id=? '
                               'ORDER BY contract_date DESC,observation_id DESC LIMIT 1', (complex_id,)).fetchone()
    candidate = {**dict(complex_row), **dict(first)}
    candidate['name'] = candidate.pop('apartment_name')
    candidate['coordinates'] = (None if complex_row['latitude'] is None else
                                {'latitude': complex_row['latitude'], 'longitude': complex_row['longitude'],
                                 'review': json.loads(complex_row['coordinate_review_json'])})
    coverage = [json.loads(row[0]) for row in connection.execute('SELECT provenance_json FROM coverage WHERE sgg_cd=?', (candidate['sgg_cd'],))]
    facilities = []
    if candidate['coordinates']:
        for scope in coverage:
            facilities.extend(_nearby_facilities(connection, (complex_row['latitude'],complex_row['longitude']),
                                                 scope['category'], scope['coverage_area']['radius_m']))
    for facility in facilities:
        facility.pop('_distance_m', None)
    relations = [json.loads(row[0]) for row in connection.execute('SELECT m.provenance_json FROM reviewed_relations m '
                  'JOIN rental_observations o ON o.observation_id=m.observation_id WHERE o.complex_id=? ORDER BY o.contract_date DESC,o.observation_id DESC LIMIT ? OFFSET ?',
                  (complex_id, MAX_DETAIL_OBSERVATIONS, offset))]
    metadata = dict(connection.execute('SELECT key,value FROM metadata'))
    return {**state, 'status': 'ok', 'complex': candidate, 'observations': [dict(row) for row in rows], 'fields': fields,
            'coverage': coverage, 'facilities': facilities, 'reviewed_relations': relations,
            'unsupported_fields': json.loads(metadata['unsupported_source_fields']),
            'observation_limit': MAX_DETAIL_OBSERVATIONS, 'offset': offset, 'total_observations': total,
            'next_offset': offset+MAX_DETAIL_OBSERVATIONS if offset+len(rows)<total else None,
            'previous_offset': max(0, offset-MAX_DETAIL_OBSERVATIONS) if offset else None}

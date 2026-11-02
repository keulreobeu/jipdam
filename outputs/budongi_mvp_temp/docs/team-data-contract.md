# 3인 데이터 수집 — 확정된 공통 스키마와 제출 규칙

2026-10-13 확정. 계약: [TEAM-DATA-001](specs/16_team_collection_schema_spec.md). 결정: [ADR-008](adr/ADR-008-team-collection-contract.md). 실행: [Task](tasks/team-data-contract.md). 실제 DB 점검: [검증 기록](team-data-contract-validation-20261013.md).

이 문서를 세 담당의 수집 전 기준으로 사용한다. `team_collection_v1`은 **제출 파일 계약**이다. 현재 프로그램이 모든 신규 종류를 적재한다는 뜻은 아니다. 기존 수집·키·매칭 승인 경계를 유지하며 분담안의 확장 목록을 새 MVP 요구로 확정하지 않는다.

## 1. 지금 확정한 DB 구성

```text
각 담당: 등록된 출처 → 변경 없는 raw + 출처/범위/해시 manifest
                         ↓ 원본 위치·단위·버전 보존
                      normalized 종류별 파일 + schema + validation
                         ↓ 통합 담당의 계약/무결성 대사
  거래 → 기존 canonical v3 새 스냅샷       통계 → 별도 statistics_v1
  시설·건물특성·교통·공간·규약 → 제출 보존; 새 어댑터/스키마 구현 대기
                         ↓ 별도 승인·사람 검수 후
                관계/좌표/커버리지 → 추천 serving 스냅샷(후속)
```

| 영역 | 현재 구성·재사용 | 신규 자료 처리 |
|---|---|---|
| 거래 | `canonical_real_estate_v3`: sources/regions/batches/raw_items/observations/complexes/buildings/addresses/match_candidates 등 | 등록 rental/sale만 현행 어댑터 가능. 기존 MOLIT 3개 출처와 원본 재사용 |
| 통계 | `statistics_v1`: datasets/series/stat_observations/source_files/import_batches/metadata_reviews | 제공 30개 파일 유지. HUG 등 새 layout/주기는 등록·어댑터 후 적재 |
| 추천 | `rental_v1`: rental_complexes/facilities/coverage/observation_matches | 현재 합성 추천만 실행 가능. source_unverified 자료는 실제 추천 준비 완료가 아님 |
| 역사 | `serving_v1`/2023 이하 계약 | 최신 자료를 넣지 않는다 |
| 신규 도메인 | 현행 거래 importer에는 facility/building_profile/transit/geometry/restriction 레코드 지원 없음 | 공통 제출 파일에 보존, 기존 DB에 임의 열/행 삽입 금지 |

기존 canonical의 `complexes`는 **공식 출처 범위의 엔터티**다. 여러 출처가 같은 실제 단지인지 확정한 전 출처 마스터가 아니다. 원본 DB·이전 스냅샷은 변경하지 않고 기존 재구성 명령을 사용한다. [기존 공유 원본/복원 안내](shared-data.md).

## 2. 공통 식별자와 주소

| 필드 | 타입/필수성 | 확정 규칙·기존 DB 대응 |
|---|---|---|
| `source_id` | TEXT, 필수 | 공동 등록된 데이터셋/서비스 ID. 기존 molit_apt_rent / molit_apt_trade_general / molit_apt_trade_detail 그대로 |
| `dataset_id` | TEXT, 필수(등록 메타데이터) | 제공기관 데이터셋 ID 또는 내부 등록 ID. 단지/행 ID가 아님 |
| `identifier_namespace` + `source_entity_id` | TEXT, 공식 엔터티 ID가 있을 때 둘 다 필수 | 기관+서비스+ID필드/식별 범위. 원문 ID 유지. 엔터티 종류도 등록한다 |
| `source_record_id` | TEXT/NULL | 출처가 실제 제공한 레코드 ID만. 없으면 내부 관측 키로 채우지 않음 |
| `complex_id`, `building_id`, `address_id` | TEXT/NULL | 통합 경로의 불투명 내부 ID. 수집 단계에서는 비워도 됨. 기존 ID를 재사용하고 이름/주소 hash로 발급 금지 |
| `entity_level` | TEXT, 레코드 종류별 필수 | complex/building/unit/facility/region/network/geometry. 노선·측정소 등의 구체적 하위 타입은 schema에 명시 |
| `sgg_cd` | TEXT(5)/NULL | 공식 시군구 코드 근거가 있을 때만. 거래는 현행 계약상 필수 |
| `bjd_cd` | TEXT(10)/NULL | 전체 법정동코드. 행정동 코드를 넣지 않음. 코드 체계·기준일/출처를 schema에 기록 |
| `adm_cd` | TEXT/NULL | 공식 행정동 코드가 제공되면 별도 보존. 길이/버전은 원천 정의에 등록; bjd_cd로 변환 추정 금지 |
| `region_name_raw`, `region_path_raw` | TEXT/NULL, 지역 집계에는 필수 | 표의 서울/중구 등 상위 문맥. 이름만으로 코드 확정 금지 |
| `road_address_raw`, `jibun_address_raw` | TEXT/NULL | 두 주소 원문 별도, 하나가 없으면 다른 주소로 복제 금지 |
| `legal_dong`, `jibun`, `apartment_name` | TEXT/NULL | 기존 관측의 원천 문자열. 거래 apartment_name은 필수이며 식별키가 아님 |
| `main_number`, `sub_number`, `land_code` | TEXT/NULL | 표준 주소는 본번/부번 4자리·토지구분 1자리. 공식 성분 근거가 있을 때만 표준화 |
| `pnu` | TEXT/NULL | 원천이 제공한 필지 식별값과 코드 정의 보존. 없는 성분을 보충해 생성하지 않음 |

**현행 주소 매핑:** 검증된 10자리 `bjd_cd`가 있고 앞 5자리와 `sgg_cd`가 일치하면 뒤 5자리를 canonical `addresses.legal_dong_code`로 매핑한다. 현행 이 열에 10자리 전체코드를 넣으면 CHECK 오류다. 표준 주소 생성에는 위 코드 성분·본번·부번·토지구분·`address_basis`가 모두 필요하다. 불완전 주소는 원문으로 보존하고 address_id는 NULL이다.

**ID 예:** MOLIT `aptSeq`는 기존 namespace `molit_apt_trade_detail:aptSeq`의 단지 ID이며 거래/건물 ID가 아니다. 같은 숫자를 가진 K-apt ID와 합치지 않는다. 공식 ID 없는 전월세 관측은 원본 위치로 추적하며 매칭 후보를 pending으로 보존한다. 건축물 ID가 있어도 단지 소속을 자동 확정하지 않는다. 공개되지 않은 호실을 만들지 않는다.

향후 여러 공식 외부 ID를 하나의 내부 단지에 붙이는 관계는 `identifier_namespace, source_entity_id, entity_level, internal_entity_id, evidence_ref, review_status, reviewed_by, reviewed_at_utc`를 보존하는 별도 관계 계약을 따른다. 현재 complexes의 UNIQUE(namespace, ID)를 수정하거나 다른 출처 ID로 덮어쓰지 않는다. 물리적 관계 테이블/확정 링크는 수집 후 별도 Task다.

## 3. 모든 정규화 레코드의 공통 열

아래는 파일의 공통 envelope다. 같은 파일/배치에 일정한 메타데이터는 manifest/schema에 한 번 두고 레코드에서 참조해도 된다. 모든 값은 그 참조까지 포함해 복원 가능해야 한다.

| 필드 | 타입 | 필수/결측 규칙 |
|---|---|---|
| `delivery_schema_version` | TEXT | 필수, `team_collection_v1` |
| `source_id`, `batch_id`, `mapping_version`, `record_type` | TEXT | 필수, 중앙 등록과 동일. 버전 없는 자동 추정 금지 |
| `source_file_ref` | TEXT | 필수, 패키지 루트 상대 `/` 경로; 절대경로·`..` 금지 |
| `source_content_sha256` | TEXT(64) | 필수, 소문자 hex; 원본 bytes의 SHA-256 |
| `source_section` | TEXT | 필수. XML items/CSV 단일 section/XLSX 시트/JSON 선택 pointer/공간레이어 등 실제 위치 정의 |
| `source_row_number` | INTEGER > 0 | 행 기반 필수. API 페이지 item은 페이지 파일 내 1부터. CSV는 헤더 다음 첫 데이터행 1부터. XLSX는 실제 1-based 시트 행 |
| `source_column_number` | INTEGER > 0/NULL | 통계셀 기반 필수, 실제 시트 열. 행 기반은 NULL |
| `source_feature_id` | TEXT/NULL | 행이 없는 공간 feature에서 필수. feature ID가 없으면 보존 파일 내 안정된 위치 번호와 순서 규칙을 schema에 등록 |
| `source_retrieved_at_utc` | TEXT/NULL | 실제 외부 수집시각, UTC ISO-8601 `...Z`. 제공 파일에서 모르면 NULL |
| `provided_at_utc` | TEXT/NULL | 사용자/팀 전달시각, 알고 있을 때만 |
| `staged_at_utc`, `loaded_at_utc` | TEXT/NULL | 단계가 실행됐을 때 그 시각. 수집/공표/기준일 대체 금지 |
| `source_published_at_utc` | TEXT/NULL | 실제 제공기관 공표시각만, 날짜만 알려지면 별도 `source_published_date` |
| `source_date`, `source_effective_from`, `source_effective_to` | TEXT/NULL | 날짜 `YYYY-MM-DD`; 출처 기준일/유효기간이 있는 경우만 |
| `validation_status`, `validation_reason` | TEXT, 사유는 NULL 가능 | 제출 상태 accepted/excluded/rejected. 제외/거부는 사유 필수 |
| `quality_status` | TEXT | 실제 미검수 `source_unverified`, 합성 `synthetic_only`. 통계 기존 상태 `user_supplied_pending_review`를 명시적으로 보존 |

원본 위치 식별은 출처+파일 참조+해시+section+행/셀/feature 위치의 조합이다. 기존 raw_item_id/observation_id/file_id 알고리즘은 각 저장기에서 그대로 재사용한다. 새 공통 hash 알고리즘으로 기존 PK를 다시 계산하지 않는다. 원본 위치 식별자와 정규화 매핑 버전, 실제 거래 고유 ID는 서로 다르다.

`contract_date`는 계약일, `period_key`는 통계 주기/기간, `observed_at_utc`는 실시간 관측시각, `snapshot_date`는 배치 조회 기준일이다. 이들을 공통 date 한 열에 합치지 않는다. 통계 월 `YYYY-MM`/주 `YYYY-MM-DD`와 거래 조회월 `contract_month=YYYYMM`의 현행 형식도 유지한다. 파일명 날짜·사용자 업데이트 메모는 별도 원문 메타데이터다.

현행 파일 staging의 `retrieved_at_utc`는 보존 복사 당시 `utc_now()`이며 실제 제공 파일 다운로드 시각을 뜻하지 않는다. 신규 제출에서는 이를 `staged_at_utc` 의미로 보존하고 실제 다운로드 시각은 `source_retrieved_at_utc`에 별도로 둔다. 기존 XML batch_files.retrieved_at_utc는 기록된 실제 조회 시각이다. 기존 열을 일괄 재해석하거나 과거값을 수정하지 않는다.

## 4. 단위·결측·좌표

- 거래 `deposit_krw/monthly_rent_krw/price_krw`: 64비트 범위의 원 정수. 원천 만원은 정확한 Decimal × 10,000, 정수 여부 검증 후 변환. 원문·원단위·변환식 기록. bool/비유한 수·정밀도 잃은 Excel 금액 거부.
- `area_sqm`: ㎡, 거래는 양수. `distance_m`: m, 계산 결과는 방법과 버전을 함께 기록. 기간 비용은 `amount_krw, billing_period, cost_scope`를 함께 두고 월세·관리비·단가를 같은 비용으로 합산하지 않는다.
- 통계 `value_decimal`: 정확한 Decimal 문자열, `value_numeric`: 조회용 REAL, `unit_code/unit_status`: 원천 단위/검수 상태. 지수 기준기간과 금액/건수/비율/배수 구분. 통계 평균 만원은 소수일 수 있어 거래 정수 규칙을 적용하지 않는다.
- 비율은 `percent`(0~100 표현)와 `ratio`(0~1 표현)를 구분해 원천 정의를 기록한다. 모든 지수에 0~100 범위를 강제하지 않는다. 단위 미확인은 provisional이며 환산하지 않는다.
- JSON은 `null`, CSV는 빈 셀을 NULL로 사용한다. 문자열 `NULL/None/NaN/-`의 의미는 출처별 mapping에 등록하고 원문을 보존한다. 확인된 0과 false만 그대로 저장한다. 불명확한 boolean은 NULL/unknown이다.
- 좌표는 `latitude/longitude`(decimal degrees, WGS84), 둘 다 있거나 둘 다 NULL. 범위 -90~90/-180~180 및 숫자/유한성을 검증한다. 교환 CRS 이름은 `EPSG:4326`; 축은 열 이름으로 고정한다. GeoJSON positions는 `[longitude, latitude]`를 따른다. [RFC 7946 §3.1.1/§4](https://www.rfc-editor.org/rfc/rfc7946).
- `source_x/source_y/source_crs/source_axis_order`, `coordinate_method`, `coordinate_evidence_ref`, `coordinate_review_status`를 별도 보존한다. CRS 미확인은 변환 대기이며 표준 좌표 NULL이다. 지오코딩·단지 대표점·건물 입구·역 출입구는 같은 점으로 취급하지 않는다.
- 공간 원본은 PBF/GPKG/GeoJSON/WMS 응답 등 실제 형태 그대로 둔다. `geometry_ref/geometry_type/source_crs/layer_id/scenario/event_date`로 참조하며 이미지(WMS)를 polygon으로 위장하지 않는다. WGS84 도 단위 차이를 m로 쓰지 않는다. 현재 추천은 직선거리이며 보행거리/시간으로 표시하지 않는다.

## 5. 종류별 최소 스키마와 담당

공통 열에 아래 typed 필드를 더한다. 필수라고 명시한 것 외에는 **원천에 없으면 NULL**이고 원문/미제공 사유를 보존한다. 이름은 팀 교환 필드이며 해당 기관 API의 실제 응답 태그라는 주장이 아니다. 실제 태그·단위→교환 열의 매핑은 수집 후 확인한다.

| 담당/record_type | 필수 도메인 필드 | 선택 보존 필드·주의 | 현재 적재 지원 |
|---|---|---|---|
| 1 / `rental`, `sale` | sgg_cd, apartment_name, contract_date, area_sqm; rental은 deposit_krw+monthly_rent_krw, sale은 price_krw | legal_dong/jibun/floor/build_year/source_complex_id/source_building_id/source_record_id/원문 취소·정정. rental 내부 kind jeonse/wolse는 월세 0/>0의 기존 규칙 | CANONICAL-001 지원. 공식 ID는 official_identifiers.namespace/basis 필요. 기존 975 query 재사용 |
| 1 / `regional_statistic` (HUG 등), 공통 통계 | metric_code, region_path_raw, frequency, period_key, unit_code, value_status(numeric/missing), dimensions_json; numeric이면 value_decimal | 분모/모집단/주택유형/상품범위/source_view/공표·기준기간/잠정 단위. 사고율 미제공이면 숫자 생성 금지 | 기존 30개 등록 통계만 지원; HUG 주기/layout/매핑은 추가 등록 대기 |
| 1 / `facility` (어린이집/학교/병원/약국), 2·3도 공통 | name, facility_type_code, entity_level=facility | source_entity_id+namespace, 주소, 좌표 검수, 기관유형/시설상태. 정원·현원·교원·진료과는 단위/기준일이 있는 도메인 typed 열 | 신규 제출 가능; 현행 rental은 station/supermarket/park/hospital 4종만. 좌표/출처 검수 전 serving 금지 |
| 2 / `facility` (역/정류소/상가/공원 등) | 동일 facility 필수 필드 | 원천 업종/기관/운영자 코드. 역·정류소를 노선·승강장·출입구와 구분. 분류 매핑 미확인은 원코드 보존 | 신규 어댑터 대기. 마트와 편의점을 임의로 같은 superclass로 승격하지 않음 |
| 2 / `transit_route`, `transit_stop_link` | route: namespace+source_entity_id+name; link: route_namespace+source_route_id+stop_namespace+source_stop_id+stop_sequence(INTEGER≥0) | 방향/운영자/운행유효기간. 참조 무결성/도시 범위 검수 전 pending | 미지원, raw/normalized 제출 보존 |
| 2 / `time_observation` (도착/대기질 등) | metric_code, subject_namespace+source_subject_id, observed_at_utc, unit_code, value_status; numeric이면 value_decimal | 측정/예보·응답시각·유효기간·station/route/stop 관계. 한 시각의 값은 단지 고정 속성이 아님 | 미지원, 통계 주간/월간 parser로 강제 적재 금지 |
| 2 / `spatial_layer` (침수/재난/사고 등) | layer_id, representation(image/vector/raster), geometry_ref, source_crs(미확인이면 명시 unknown) | scenario/event_date/return_period_raw/license_ref/해상도. 과거 이력과 예상 시나리오 구분 | 미지원; 이미지 기반 단지 침수 판정 금지 |
| 3 / `complex_profile`, `building_profile`, `unit_profile` | entity_level, namespace+source_entity_id 또는 원본 위치, name 또는 원천 라벨 | use_approval_date(날짜), households_count/parking_count/elevators_count(정수≥0), floors_above_ground/floors_below_ground(정수≥0), area_sqm, heating_type_raw/structure_raw. 전용/공용 면적 구분 | 현재 buildings는 identity 골격만; 이 특성 열은 추가 스키마 대기 |
| 3 / `network_segment` (보행) | network_version, segment_namespace+source_segment_id, geometry_ref, source_crs | source_node_from/to, direction_raw/access_raw/steps_raw/slope_raw, 길이와 계산 방법, 추출시각/라이선스 | 미지원; route 계산/경사 누락 대체는 후속 |
| 3 / `restriction_evidence` (반려동물 등) | subject_namespace+source_subject_id 또는 원본 위치, restriction_type, status(allowed/conditional/disallowed/unknown) | 조건/적용범위/확인일/근거문서. unknown 외 상태는 evidence_ref+reviewed_by+reviewed_at_utc 필수. 관광시설 동반 가능과 아파트 규약 구분 | 미지원; 근거 없으면 unknown. 자료 없는 false 생성 금지 |

공시가격은 거래 price_krw와 다르다. `record_type=assessed_value`는 `metric_code=official_assessed_value`, `entity_level`, `amount_krw`(정수≥0), `assessment_date`(YYYY-MM-DD), `area_basis`, `subject_namespace/source_subject_id` 또는 원본 위치를 필수로 제출한다. 확인되지 않은 평가 기준은 NULL/미제공 사유로 보존하고 정규화 적재 대기다. 실제 호실/평가대상/가격 기준이 확인되기 전 단지 전세 위험에 자동 연결하지 않는다.

관리비는 `record_type=cost_observation`: 대상 계층/식별 근거, `period_key/frequency`, `billing_period/cost_scope`, `value_basis` 필수다. `value_basis=total_amount`이면 `amount_krw`(정수≥0)가 필수이며 원천이 단가/집계 평균이면 `value_basis=unit_price/average`와 `value_decimal/unit_code`가 필수이고 amount_krw는 NULL이다. 정수 총액을 만들어내지 않는다. 에너지는 `record_type=energy_observation`: 대상 계층/식별 근거, `period_key/frequency`, `energy_type`, `value_decimal/unit_code` 필수다. 기준기간/단위 미확인 자료는 원문과 NULL/사유를 보존하고 적재 대기다. 세 종류 모두 현행 importer 미지원이며 수집 후 typed 어댑터 Task로 연결한다.

역/시설 출처 중복도 원본별 별개 관측을 유지한다. serving용 분류 투영은 station/supermarket/park/hospital만 명시적으로 매핑하고 나머지는 미지원 목록에 남긴다. 학교 거리로 실제 배정 학교를 확정하지 않는다.

**역할:** 1번은 거래/통계 기존 공유 패키지와 완료 기록부터 확인하고 중복 수집을 제외한다. 2번은 시설·교통·환경의 위치/영역·커버리지 근거를 책임진다. 3번은 건물·단지·네트워크 원본과 **통합 ID 등록/충돌 보고**를 맡는다. 각자의 mapping/건수/오류/권한 검수는 각자가 책임지고 3번에 모두 넘기지 않는다. 실제 이름·범위·기간은 수집 예약에서 정한다. 새 수도권 확장·같은 샘플 구 선정은 이번에 확정하지 않는다.

## 6. 등록·제출 패키지

파일명을 자유롭게 두더라도 아래 폴더 역할과 manifest 참조를 지킨다. 기존 MOLIT/통계 패키지는 원형을 보존하고 해당 원본 manifest를 연결하는 **호환 설명**만 더한다. 새 형식으로 기존 원본을 다시 포장/복사할 필요는 없다.

```text
<source_id>/<batch_id>/
  raw/                         # 원본 bytes, 원래 파일명은 manifest에 별도
  normalized/<record_type>.jsonl # 기본 UTF-8 JSONL; 종류별 typed 필드
  schema.json                   # 열/타입/단위/NULL/원태그 매핑·버전
  manifest.json                 # 범위·출처·시간·파일별 hash/건수
  validation.json               # 대사·오류·결측·중복·미확정 관계
  README.md                     # 승인된 재현/오프라인 파싱 명령
  code/                         # parser 또는 저장소 commit+모듈 참조
```

CSV는 UTF-8, 구분자·인용 규칙을 schema에 명시하고 코드·정밀 수치는 TEXT로 읽는다. JSONL의 고정 소수 통계는 문자열이며 금액은 정수다. 소수 원문은 raw에 남긴다. XLSX는 raw로 받고 normalized 제출은 JSONL/CSV를 사용한다. 현행 stage-file의 JSON은 **일반 JSON+items_path**이며 JSONL을 직접 지원하지 않는다. 기존 rental/sale importer에 넣을 때는 등록된 CSV/JSON/XLSX 형태로 명시적 변환하고 변환본도 별도 계보를 남긴다. 공간 데이터는 raw 파일 + feature/레이어 메타데이터 normalized로 제출할 수 있다.

**schema.json 필수:** delivery_schema_version/source_id/record_type/mapping_version, columns의 name/type/nullable/unit/required_when, 원태그/열·섹션 선택, 원단위→정규화 변환식, 결측 marker, 식별자 namespace/basis, 엔터티/지역코드 정의, CRS/축/날짜 의미. 미확인 원필드는 `unmapped_fields`와 원문 위치에 남긴다. 같은 source_id의 서로 다른 레코드 종류도 record_type별 계약을 둔다.

**manifest.json 필수:** delivery_schema_version, source_id/dataset_id/provider/documentation_url, batch_id/mapping_version/담당자, record_url/approval_ref(수집 실행 승인), 출처 라이선스 원문 또는 license_ref와 license_review_status(pending/verified/rejected), 요청 지역/기간/필터/페이지 또는 영역, source_retrieved_at_utc/provided_at_utc/staged_at_utc, snapshot_date(있을 때), quality_status, 파일별 path/format/bytes/sha256/section/rows, 요청별 collection_status/expected_rows/received_rows, raw/accepted/excluded/rejected 총수, 누락/오류/원천 미제공 날짜. URL의 인증 쿼리·키 값은 기록하지 않는다.

모르는 라이선스·단위·시각은 pending/NULL로 명시해 원본 증거를 보존한다. 사용권 불명확 자료의 배포·분석 적격성은 별도 검수 후 결정한다. 현행 Registry의 approved는 **수집 범위 승인**이며 출처 사실/사용권/추천 적격성 verified와 다르다. 신규 출처를 이번 계약만으로 approved 등록하지 않는다.

**validation.json 필수:** 대사 수치, section별 행/셀/feature 수, rejected 위치+사유, 컬럼별 결측 수, 중복 원본/원본 위치/유사 엔터티를 각각 구분한 건수, code/coordinate/FK 충돌과 pending 관계, 미매핑 필드, 재실행 결과, parser commit/매핑/실행 버전, 검증시각. 대용량 오류 목록은 별도 파일 경로+hash로 참조한다.

최종 ZIP 자체의 SHA는 자기 manifest에 넣지 않고 COLLECT-001 Issue에 기록한다. 수집 전 완료·닫힌/예약 Issue 검색과 재확인, 업로드 전 결과/최종 해시, 업로드 뒤 개별 링크는 [수집 절차](../../../docs/data-collection.md)를 따른다. 원본·DB·ZIP·API 키는 Git 제외다. 이번 작업에서는 원격 기록/수집/업로드를 실행하지 않는다.

## 7. 상태·대사·재실행

| 차원 | 제출 계약 | 기존 DB 대응/주의 |
|---|---|---|
| 수집 | complete/complete_zero/partial/failed/not_collected | canonical.coverage 동일 값. 성공 0건과 미수집/실패 구분. 전체 페이지 완료만 수집 complete |
| 정규화 | accepted/excluded/rejected | 거래 accepted→staging_items.valid, 기간 제외만 excluded→outside_period. 다른 제외 이유는 별도 adapter 계약 없이 outside_period로 넣지 않음 |
| 값 | numeric/missing 또는 typed NULL | 통계 numeric/missing 그대로. 타입 오류는 missing으로 감추지 않음 |
| 사실 품질 | source_unverified/synthetic_only/기존 통계 상태 | raw 수집 성공을 verified 추천 상태로 승격 금지 |
| 관계 | pending/confirmed/rejected + 근거/검수자/검수시각 | canonical match_candidates는 pending만 지원. confirmed를 CHECK 위반으로 직접 입력 금지. rental 관계 confirmed는 별도 사람 검수 필수 |
| 좌표·단위·라이선스 검수 | pending/verified/rejected | manifest/검수 보고에서 독립 관리. 하나의 verified로 전체 항목을 합치지 않음 |
| 시설 탐색 커버리지 | complete/partial/unknown + 실제 검수 영역/기준일 | 수집 페이지 complete와 다름. 지역 목록만으로 경계 바깥 반경까지 완전하다고 추론하지 않음 |

원본행/셀/feature 수 = accepted + excluded + rejected. 전달 레코드에는 거부도 validation 위치로 남겨 숨기지 않는다. 통계 accepted는 numeric+missing이며 missing은 거부가 아니다. 파일/section 기대 건수와 실제 수를 대사한다. 기대 총수 제공 안 됨은 NULL이며 임의로 실제 수를 expected로 채우지 않는다. 파일 내부 대사 성공과 제공기관 전체 커버리지 검수는 별도다.

같은 batch_id+mapping_version+입력 서명 재실행은 신규 0, 입력 변경은 오류다. 새로운 bytes/기준시각/개정은 새 배치나 명시적 매핑 버전으로 남기고 과거 관측을 보존한다. 같은 금액·면적·날짜의 서로 다른 행, 매매 일반/상세, dashboard/상세표를 병합하지 않는다. 처리 실패는 실패 보고를 보존하되 최종 성공 DB로 게시하지 않는다. 현행 거래 기본 strict rollback을 유지한다.

**제출 수락 순서:** 등록/승인·사용권 상태 확인 → 파일 hash/안전한 경로 → section/행·단위/코드/NULL 검사 → 전체 대사 → 지원 record_type만 새 출력에 적재 → PK/FK/무결성/원본 조인 → report 게시. 미지원 종류는 `adapter_pending`으로 수락 보존하고 적재 완료로 세지 않는다. 실제 신규 입력의 이 검사 자동화는 별도 구현 Task다.

시설 제출의 첫 자동 검증 구현은 [FACILITY-PACKAGE-001](specs/29_facility_package_validation_spec.md)과
[TASK-BENCH-FACILITY-001](tasks/facility-benchmark.md)로 추적한다. 첫 범위는 CSV/JSONL의
facility_all_status_rows_v1 프로파일이며 전체 team_collection_v1의 모든 제출 레이아웃이나
실제 데이터 적재 지원을 의미하지 않는다. 실제 구현/독립 검증 상태는 해당 Task를 따른다.

## 8. 수집 후에 확정할 항목

| 후속 결정 | 필요한 증거 | 책임 역할 | 그 전 저장 상태 |
|---|---|---|---|
| 실제 API 태그/파일 layout·단위·날짜 매핑 | 공식 필드 설명+실제 raw 샘플·전 페이지/시트 대사 | 각 수집자 | 원문/미매핑/단위 provisional; 미지원은 adapter_pending |
| K-apt↔건축물↔MOLIT 동일 단지/건물 관계 | 공식 ID 범위/주소 성분/불일치 사례·검수자 | 3번 통합+각 원천 담당 | 출처 엔터티 분리, FK NULL/후보 pending |
| 원천 취소/정정/동일 거래 연결 | 실제 제공 필드·기관 정의·수정 이력 | 1번 | 독립 관측·원문 상태 미확인 |
| 실제 대표좌표·변환 CRS·오차 기준 | 원 CRS/축/원점 의미/변환 근거·샘플 지도 검수 | 2번 시설·3번 단지 | 원좌표 보존, 표준 좌표 NULL 또는 pending |
| 시설 중복·원천 분류→표준 분류·조회반경 완전성 | 기관 ID/분류표·서비스 범위/경계·갱신 시점 | 시설 담당 | 원코드/별개 관측, coverage unknown/partial |
| 통계 지역코드/주기/layout·HUG 분모/비율 의미 | 표 문맥·공식 정의·원문 단위·라이선스 | 1번 | 통계 계층 보존, 지역 FK NULL, 비율 계산 없음 |
| 침수 판정/원공간 접근·사용조건·시나리오 | 분석 가능한 자료/해상도·허용 용도·실제 overlay 검증 | 2번 | image/vector/raster 원형, 단지 판정 없음 |
| 보행 연결성·경사·계단·경로/시간 계산 | 네트워크 누락/연결 검사·길이/속도 모델·버전 | 3번 | graph 원본, 추천은 기존 직선거리 |
| 규약/반려동물 허용·관리비 대상/기간 | 실제 문서·확인시각/검수자·비용범위 | 3번 | unknown/원문 조건; 근거 없는 허용/0 없음 |
| 추천 후보 적격성·지표/가중치·위험 해석 | 사람 검수된 연결/좌표/커버리지·제품 승인 | 통합 담당+사용자 | 적재와 별도; 실제 추천/위험 점수 미생성 |

실제 담당자, 공동 시범 지역/기간, 신규 수집 시작·확장 범위는 아직 결정하지 않는다. 기존 서울 25구 MOLIT 원본과 통계 30개는 재사용 대상이다. 전세 사고율/사기확률·통학 배정·보행 소요시간은 이번 스키마 결정으로 산출을 승인한 것이 아니다.

## 9. 이번 적용 Plan과 검토 기록

순서: 기존 계약/코드/실제 DB 읽기 → 위 공통 계약·호환표 확정 → Spec/ADR/Task/원장 연결 → 읽기 전용 구조/무결성·SDD 검증. 변경 대상은 문서 7개, 새 서비스/클래스 0개다. 단일 계약 문서 작업으로 순차 적용한다. 제품 코드/DB 마이그레이션은 후속이다.

Scope: 사용자가 요청한 수집 전 계약 확정과 수집 후 결정 분리. 기존 해결책은 canonical raw/배치/ID/typed 거래와 별도 통계 저장기다. 신규 서버·ORM·단지 매칭기·수집기를 추가하지 않는다.

Architecture 검토: 기존 출처별 ID를 전 출처 단지 마스터로 간주하면 잘못된 FK가 생긴다. namespace/계층·NULL·후속 관계 검수로 처리했다. 통계/공간/실시간 사실은 거래와 분리했다. 모두 현재 요청의 호환 계약 범위다.

Code quality 검토: 기존 key/normalize/파일 어댑터를 재사용한다. JSONL과 일반 JSON, 실제 수집 시각과 staging 복사 시각, 전체 법정동과 뒤 5자리 코드의 차이를 명시했다. 코드 변경 없음.

Tests 검토: 새 제품 acceptance suite는 작성하지 않는다. 실제 DB의 구조/열/FK를 코드의 in-memory 스키마와 대조하고 integrity/FK/건수를 검사한다. 스키마/입력 자동 validator와 신규 도메인 어댑터 테스트는 구현 Task에서 작성한다. 수집 후 품질 완료를 문서 AC로 대체하지 않는다.

Performance 검토: 대용량 거래행을 시설 수만큼 중복 저장하는 사전 단지×시설 Cartesian table은 제출 요구에서 제외한다. 행 단위 계보와 별도 시설/공간 원본을 유지한다. 실제 serving 인덱스/경로/지연은 신규 구현 후 계측하며 이번에 성능 수치를 확정하지 않는다.

실패 경로: 해시/건수 불일치는 최종 적재 실패, namespace/주소 충돌은 미연결 보고, 미지원 record_type은 adapter_pending, CRS/사용권 미확인은 분석·공유 적격성 검수 대기, 수집 실패는 complete_zero로 바꾸지 않는다. 현행 strict 검증은 기존 테스트/Spec, 새 도메인은 후속 구현 검사로 연결한다.

독립 외부 CLI/서브에이전트 리뷰는 실행하지 않았다. gstack 시작 도구의 Git Bash 실행은 OS 접근 오류로 실패했고 자동 리뷰 로그/완료 대시보드 credit은 없다. 수동 계약 검토·실제 DB·SDD 검사 결과만 [검증 기록](team-data-contract-validation-20261013.md)에 보고한다.

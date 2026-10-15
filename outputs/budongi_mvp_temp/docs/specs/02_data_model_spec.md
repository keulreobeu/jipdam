# Data Model Spec

## CURRENT

- `src/budongi/storage.py`는 `serving_v1` SQLite 스키마의 `snapshots`, `apartments`, `locations`, `facilities`, `transactions`를 정의한다.
- 정규화된 `apartments.csv`와 `transactions.csv`를 새 snapshot ID로 한 번 적재한다. 입력 파일 SHA-256, 출처·원천 ID·`valid_date`를 저장한다. 이미 사용한 snapshot ID를 덮어쓰지 않는다.
- 역사 importer는 snapshot date를 2023-12-31 이하로 제한한다. `locations`는 아파트 CSV의 선택 필드로 적재할 수 있고 `facilities` 적재기는 아직 없다.
- `data/provisional/`의 임시 카탈로그와 API 원본은 실측 역사 자료가 아니다. `data/historical/serving.sqlite3`가 존재한다는 사실만으로 실제 스냅샷 적재를 뜻하지 않는다.
- `src/budongi/rental_storage.py`에는 기존 역사 DB와 분리된 `rental_v1` 합성 저장 계약이 추가됐다. XML 원문 행 파서와 정규화 입력의 계보·시설 커버리지·검수 매칭 저장은 동작하지만, 공식 전월세 주요 필드/단위 검증·원천 매핑·환산과 확정된 서울 실수집은 MOLIT-001 경로에서 완료했다. 사람 검수 좌표·시설·추천 매칭은 별도다.

## 계약

2026-10-12 최신 MOLIT 수집 경로는 [MOLIT-001](12_molit_collection_spec.md)을 따른다. 전월세 `rental_v1`과 매매 `sale_observations_v1`은 별도 관측 DB이고 품질은 `source_unverified`다. `staging.sqlite3`의 `raw_files`/`staging_items`는 모든 완료 원본 행의 원문·위치·해시·정규화 상태/기간 제외 사유를 보존한다. 전체 거부 사유는 별도 보고하고 DB 전체 게시를 거부한다. 원본 행 = 유효 + 기간 제외 + 거부이며 유효 수 = 두 관측 DB 실제 수 = 원본 조인 수를 검증한다. source+file hash+row 관측 키는 실제 거래 고유 ID가 아니며 동일 값의 여러 행·일반/상세 관측은 합치지 않는다. 기존 역사 계약은 아래와 같이 유지한다.

- 단지 필수 열: `apartment_id,name,source,source_id,valid_date`.
- 거래 필수 열: `transaction_id,apartment_id,contract_date,price_krw,area_sqm,status,source,source_id,valid_date`.
- `status`는 `valid`, `canceled`, `corrected` 중 하나. 동일 `snapshot_id/source/source_id`의 최신 유효 버전을 조회하며 취소 버전은 제외한다.
- 거래 가격은 원 정수, 면적은 ㎡, 역 거리는 m. 계약일·신고일·변경일·수집 시각·효력일을 혼동하지 않는다.
- `공급액(만원)`은 공급 정보이며 `transactions.price_krw`로 승격하지 않는다.
- 원천 필드 또는 단지·거래 매칭 근거가 확인되지 않으면 역사 스냅샷으로 승격하지 않는다.

## TARGET / OPEN QUESTION

- **TARGET**: [RENT-001](10_rental_recommendation_spec.md#rent-001-req-05-최신-임대차-데이터와-계보)의 별도 최신 임대차 스냅샷과 원 정수 보증금·월세 쌍, 검수 좌표·시설·커버리지·매칭 근거를 우선한다. MOLIT-001은 확인된 전월세·매매 주요 필드와 단위를 매핑하고 실제 원본·관측을 보존한다. 확인되지 않은 종전 계약 금액 등의 필드는 원문만 유지한다. 원천 개별 ID/취소·정정의 미확인을 보존한다. 새 출처·좌표·시설·추천 연결은 별도 승인 대상이며 기존 serving_v1·역사 importer의 2023 제한은 유지한다. 기존 세 출처의 공식 ID 관계와 미확정 후보는 CANONICAL-001 승인 범위다. 2023 원본 복구·Temporal 연구는 별도 선택형 작업이다.
- **OPEN QUESTION**: 공식 HWP 상세 기술문서의 응답 필드·단위·누락 및 개별 거래 ID/취소·정정 상태 제공 여부, API 이력 재조회가 과거 상태를 보장하는지, 식별자 없을 때 버전 연결·단지 ID 검수 규칙. 이 항목을 확인하기 전 자동 매핑·매칭 결과를 확정 사실로 쓰지 않는다.

## Acceptance Criteria

- 합성 fixture에서 snapshot 재적재 방지, 미래 날짜 거부, 필수 열·상태·양수 단위 검사, 정정·취소의 최신 버전 조회가 재현된다.
- 실제 데이터 완료 선언에는 원본·매칭 검수·해시·행 수와 출처 추적 결과가 필요하다.

## 2026-10-13 통합 DB 경로

[CANONICAL-001](13_canonical_integration_spec.md)의 canonical_real_estate_v3는 기존 세 API 실제 원본과 관측을 하나의 출처·배치·지역·원본·엔터티·관측 모델에서 조회한다. 콘텐츠/원본 행과 배치 소속을 분리하고 공식 출처 ID만 확정 연결한다. CSV/JSON/XLSX는 등록된 rental/sale 목표 계약으로 같은 모델에 적재한다. 실제/합성 품질 영역은 합치지 않는다. 스키마·시간·ID·매핑·NULL·제약·증분·확장 규칙은 [실행 문서](../canonical-db.md), 최종 상태는 [Task](../tasks/canonical-integration.md)를 따른다.

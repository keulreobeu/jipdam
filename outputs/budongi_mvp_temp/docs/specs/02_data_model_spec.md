# Data Model Spec

## CURRENT

- `src/budongi/storage.py`는 `serving_v1` SQLite 스키마의 `snapshots`, `apartments`, `locations`, `facilities`, `transactions`를 정의한다.
- 정규화된 `apartments.csv`와 `transactions.csv`를 새 snapshot ID로 한 번 적재한다. 입력 파일 SHA-256, 출처·원천 ID·`valid_date`를 저장한다. 이미 사용한 snapshot ID를 덮어쓰지 않는다.
- 역사 importer는 snapshot date를 2023-12-31 이하로 제한한다. `locations`는 아파트 CSV의 선택 필드로 적재할 수 있고 `facilities` 적재기는 아직 없다.
- `data/provisional/`의 임시 카탈로그와 API 원본은 실측 역사 자료가 아니다. `data/historical/serving.sqlite3`가 존재한다는 사실만으로 실제 스냅샷 적재를 뜻하지 않는다.
- `src/budongi/rental_storage.py`에는 기존 역사 DB와 분리된 `rental_v1` 합성 저장 계약이 추가됐다. XML 원문 행 파서와 정규화 입력의 계보·시설 커버리지·검수 매칭 저장은 동작하지만, 공식 전월세 응답 필드/단위 검증, 원천 매핑·환산, 실수집은 아직 없다.

## 계약

- 단지 필수 열: `apartment_id,name,source,source_id,valid_date`.
- 거래 필수 열: `transaction_id,apartment_id,contract_date,price_krw,area_sqm,status,source,source_id,valid_date`.
- `status`는 `valid`, `canceled`, `corrected` 중 하나. 동일 `snapshot_id/source/source_id`의 최신 유효 버전을 조회하며 취소 버전은 제외한다.
- 거래 가격은 원 정수, 면적은 ㎡, 역 거리는 m. 계약일·신고일·변경일·수집 시각·효력일을 혼동하지 않는다.
- `공급액(만원)`은 공급 정보이며 `transactions.price_krw`로 승격하지 않는다.
- 원천 필드 또는 단지·거래 매칭 근거가 확인되지 않으면 역사 스냅샷으로 승격하지 않는다.

## TARGET / OPEN QUESTION

- **TARGET**: [RENT-001](10_rental_recommendation_spec.md#rent-001-req-05-최신-임대차-데이터와-계보)의 별도 최신 임대차 스냅샷과 원 정수 보증금·월세 쌍, 검수 좌표·시설·커버리지·매칭 근거를 우선한다. 지금 구현된 저장기는 정규화 입력과 합성 provenance만 검증한다. API 응답의 필드·단위가 기술문서로 확인되기 전에는 이를 매핑하거나 실제 최신 자료로 승격하지 않는다. 원천 개별 ID/취소·정정의 미확인을 보존한다. 실제 수집·매칭은 보류하며 기존 serving_v1·역사 importer의 2023 제한은 유지한다. 2023 원본 복구·Temporal 연구는 별도 선택형 작업이다.
- **OPEN QUESTION**: 공식 HWP 상세 기술문서의 응답 필드·단위·누락 및 개별 거래 ID/취소·정정 상태 제공 여부, API 이력 재조회가 과거 상태를 보장하는지, 식별자 없을 때 버전 연결·단지 ID 검수 규칙. 이 항목을 확인하기 전 자동 매핑·매칭 결과를 확정 사실로 쓰지 않는다.

## Acceptance Criteria

- 합성 fixture에서 snapshot 재적재 방지, 미래 날짜 거부, 필수 열·상태·양수 단위 검사, 정정·취소의 최신 버전 조회가 재현된다.
- 실제 데이터 완료 선언에는 원본·매칭 검수·해시·행 수와 출처 추적 결과가 필요하다.

# Data Model Spec

## CURRENT

- `src/budongi/storage.py`는 `serving_v1` SQLite 스키마의 `snapshots`, `apartments`, `locations`, `facilities`, `transactions`를 정의한다.
- 정규화된 `apartments.csv`와 `transactions.csv`를 새 snapshot ID로 한 번 적재한다. 입력 파일 SHA-256, 출처·원천 ID·`valid_date`를 저장한다. 이미 사용한 snapshot ID를 덮어쓰지 않는다.
- 역사 importer는 snapshot date를 2023-12-31 이하로 제한한다. `locations`는 아파트 CSV의 선택 필드로 적재할 수 있고 `facilities` 적재기는 아직 없다.
- `data/provisional/`의 임시 카탈로그와 API 원본은 실측 역사 자료가 아니다. `data/historical/serving.sqlite3`가 존재한다는 사실만으로 실제 스냅샷 적재를 뜻하지 않는다.

## 계약

- 단지 필수 열: `apartment_id,name,source,source_id,valid_date`.
- 거래 필수 열: `transaction_id,apartment_id,contract_date,price_krw,area_sqm,status,source,source_id,valid_date`.
- `status`는 `valid`, `canceled`, `corrected` 중 하나. 동일 `snapshot_id/source/source_id`의 최신 유효 버전을 조회하며 취소 버전은 제외한다.
- 거래 가격은 원 정수, 면적은 ㎡, 역 거리는 m. 계약일·신고일·변경일·수집 시각·효력일을 혼동하지 않는다.
- `공급액(만원)`은 공급 정보이며 `transactions.price_krw`로 승격하지 않는다.
- 원천 필드 또는 단지·거래 매칭 근거가 확인되지 않으면 역사 스냅샷으로 승격하지 않는다.

## TARGET / OPEN QUESTION

- **TARGET**: 공식 원본과 정정·취소 이력을 검수해 실제 2023 스냅샷을 고정한다. 이후 최신화는 별도 스냅샷과 Temporal Eval로 다룬다.
- **OPEN QUESTION**: 실거래 API의 개별 거래 ID가 없는 경우 버전 연결·단지 ID 검수 규칙. 이 규칙을 정하기 전 자동 매칭 결과를 확정 사실로 쓰지 않는다.

## Acceptance Criteria

- 합성 fixture에서 snapshot 재적재 방지, 미래 날짜 거부, 필수 열·상태·양수 단위 검사, 정정·취소의 최신 버전 조회가 재현된다.
- 실제 데이터 완료 선언에는 원본·매칭 검수·해시·행 수와 출처 추적 결과가 필요하다.

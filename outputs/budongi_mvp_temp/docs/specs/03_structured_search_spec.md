# Structured Search Spec

## Purpose

지역·실거래 가격·면적·준공연도·계약일 같은 명시 조건은 검증된 SQL 조회로 처리한다. 조건과 근거가 없을 때 임의 단지를 추천하지 않는다.

## CURRENT

- `search_apartments`: `district`, `max_price_krw`, `area_sqm`, `built_year_min`, `limit` 조건으로 단지를 검색한다. 가격·면적은 해당 snapshot의 최신 유효 거래를 기준으로 한다. 정렬은 `apartment_id`다.
- `search_transactions`: `apartment_id`, 계약일 범위, 최고 가격, 면적, `limit`으로 유효 거래를 검색한다. 계약일 최신순이다.
- `get_apartment_detail`: 단지 ID로 기본 정보, 위치/역 거리, 최신 유효 거래 1건을 가져온다.
- 거래 정정·취소는 동일 `source/source_id`의 최신 효력 버전을 사용한다. 결과는 snapshot, 검증된 인자, 행 수, 출처·ID·날짜가 있는 행을 담는다.
- `limit` 최대 20. SQL 값은 파라미터로 바인딩한다. 지원하지 않는 조건을 임의의 의미 검색으로 대체하지 않는다.

## TARGET / OPEN QUESTION

- **TARGET**: 실제 역사 스냅샷의 조회 결과를 사람 검수 Golden과 대조한다. 추가 정렬·통계·역 거리·전세 조건은 데이터와 Tool 계약을 확정한 뒤 별도 Spec 변경으로 도입한다.
- **OPEN QUESTION**: 거래가 없는 단지의 가격 조건 처리, 다수 거래 중 대표 가격 정의, 동일 날짜 정정 우선순위의 제품 의미를 실제 자료에서 검수해야 한다.

## Acceptance Criteria

- 합성 fixture에서 필터, 날짜 범위, 정정·취소, 조회 상한, 잘못된 인자 거부, 출처 추적을 검증한다.
- 실제 검색 정확도는 실제 스냅샷과 사람 검수 Golden이 준비되기 전까지 주장하지 않는다.

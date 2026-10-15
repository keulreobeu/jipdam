# TEAM-DATA-001 — 3인 수집의 공통 제출·DB 호환 계약

```toml
kind = "spec"
id = "TEAM-DATA-001"
status = "approved"
owner = "Codex"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-13"
approval_ref = "2026-10-13: 3인 데이터 수집 분담안에 대해 현재 DB도 반영될 수 있도록 수집 전에 통일할 스키마를 확인·확정하고 수집 후 결정은 넘겨두라는 요청"
```

## 범위

현재 DB와 호환되는 수집 전 **제출 계약**을 확정한다. 규범적인 필드·타입·단위·필수성·분담·후속 결정표는 [팀 수집 가이드](../team-data-contract.md)에 정의하며 이 Spec의 일부다. 새 자료는 `team_collection_v1` 제출 계약을 따른다. 이는 현행 SQLite 스키마 버전이나 CLI가 지원하는 새 record_type이 아니다.

현재 거래 canonical v3, 통계 statistics_v1, rental_v1, 역사 serving_v1 및 기존 원본/배치/ID를 보존한다. 이번 범위는 문서 계약이며 새 수집·키 접근·좌표 변환 실행·매칭 확정·DB 마이그레이션·추천 연결·원격 게시를 포함하지 않는다. 기존 별도 승인 경계는 유지한다. 첨부 분담안의 확장 항목을 RENT-001 MVP의 새 제품 요구로 승인하지 않는다.

## TEAM-DATA-001-REQ-01 기존 DB 호환과 분리

기존 SQLite의 실제 테이블·열·FK·건수와 코드 정의를 읽기 전용으로 대조한다. 거래는 CANONICAL-001의 rental/sale 어댑터를 재사용하고 통계는 STATS-001의 별도 저장을 유지한다. 시설·건물 특성·교통·공간·규약은 별도 typed 레코드 계약으로 제출하며 거래 `observations`나 통계 숫자셀로 위장하지 않는다. 기존 스키마에 없는 필드는 제출 파일에 보존하고 새 어댑터/추가 스키마 Task 전까지 적재 대기다.

### TEAM-DATA-001-AC-01

실제 canonical/통계/수집 rental/합성 rental 구조·건수·무결성 검사와 현재 지원/미지원 매핑표가 기록된다. 기존 원본 및 DB의 수정 없이 실행한다.

## TEAM-DATA-001-REQ-02 식별자·주소·계층

출처 ID는 `(identifier_namespace, source_entity_id)`로 보존한다. 내부 `complex_id/building_id/address_id`는 통합 담당 경로에서 발급·재사용하며 수집자가 이름이나 주소로 만들지 않는다. MOLIT aptSeq와 K-apt/건축물 ID를 같은 ID로 간주하지 않는다. 현재 출처 범위의 complex 엔터티를 전체 출처의 동일 단지로 재해석하지 않는다. 외부 ID 없는 레코드는 원본 위치로 추적하고 내부 FK는 NULL이다.

법정동 전체코드 `bjd_cd` 10자리와 시군구 `sgg_cd` 5자리, 현행 addresses.legal_dong_code의 뒤 5자리를 구분한다. 코드는 TEXT로 보존한다. 주소 원문과 표준 주소 성분은 별도로 둔다. 단지·건물·전유/호실·시설·지역 집계 단위를 구분하고 근거 없는 연결을 만들지 않는다.

### TEAM-DATA-001-AC-02

이름뿐인 단지, 서로 다른 namespace의 동일 숫자 ID, 누락/충돌 코드, 시설의 단지 FK, 단지와 건물/호실 관계에 대한 NULL·보류·충돌 처리와 기존 열 매핑이 명시된다.

## TEAM-DATA-001-REQ-03 타입·단위·시간·공간

금액은 거래 원 정수, 면적은 ㎡, 거리 m로 통일한다. 통계 Decimal·원천 단위는 그대로 보존하며 지수/평균/비율을 거래로 환산하지 않는다. 원 단위·변환식·매핑 버전과 원문을 보존한다. NULL과 숫자 0/false를 구분한다. 날짜와 시간은 가이드의 별도 필드로 보존하고 미확인 시간을 적재일로 대체하지 않는다.

좌표가 제공될 경우 원 좌표·CRS·축 순서를 보존한다. 교환용 표준 좌표는 WGS84 latitude/longitude이며 GeoJSON은 longitude/latitude 순서다. 좌표 없는 자료는 NULL이다. 변환/대표점/지오코딩 검수는 후속이다. 이미지 레이어·집계 통계·보행경로·직선거리의 의미를 섞지 않는다.

### TEAM-DATA-001-AC-03

필드 사전에 타입·단위·필수/조건부 필수·결측과 날짜/공간 의미가 정의되고 현행 5자리 주소 성분·REAL 면적·정수 금액·통계 Decimal과 호환된다.

## TEAM-DATA-001-REQ-04 원본·배치·패키지·검증

출처 등록, 수정 없는 raw, 별도 normalized, manifest, schema/단위 매핑, 검증 보고와 재현 코드를 함께 제출한다. 파일 SHA-256·행/셀/feature 위치·원문 기준시점으로 모든 정규화 값을 역추적한다. source_id/batch_id/mapping_version은 공동 등록하며 같은 배치의 다른 입력은 거부한다. 같은 값의 서로 다른 관측과 서로 다른 출처를 자동 병합하지 않는다.

수집 상태, 정규화 상태, 품질, 관계 검수, 라이선스 검수는 별도다. raw=accepted+excluded+rejected를 대사하며 수집 0건/실패/부분 완료를 구분한다. 현행 거래 staging의 valid/outside_period/rejected로 명시적 매핑한다. 신규 범용 상태를 기존 CHECK 제약에 직접 넣지 않는다. 실제 수집/Drive 공유의 COLLECT-001 사전 예약/결과/해시/후속 링크 계약은 그대로다.

### TEAM-DATA-001-AC-04

패키지 구조·필수 메타데이터·원본 위치·대사식·재실행·수집/품질 상태 분리 및 기존 어댑터의 한계가 정의된다.

## TEAM-DATA-001-REQ-05 담당과 수집 후 결정

1번은 기존 거래와 통계 원본을 먼저 재사용하고 안전·교육·의료 레코드를, 2번은 교통·상권·환경·공간 레코드를, 3번은 단지/건물·보행·규약 레코드와 통합 식별자 등록을 맡는 역할로 정리한다. 실제 담당자 이름과 신규 수집 지역/기간/사용권은 수집 예약 때 정한다. 각자 자신의 원본/정규화/품질에 책임지고 통합 담당은 PK/FK와 충돌 보고에 책임진다.

수집 후 출처별 필드 매핑, 실제 동일 단지/건물 매칭, 좌표 검수, 시설 중복/커버리지, 집계의 공식 지역 관계, 위험지표/보행 계산/추천 적격성은 별도 결정표에 남긴다. 점수·판정·새 범위/수집 시작일을 임의 확정하지 않는다.

### TEAM-DATA-001-AC-05

세 담당의 제출 record_type과 기존 DB 재사용/미지원 대상이 대응하고, 후속 결정마다 필요한 증거·책임 역할·그 전의 저장 상태가 있다.

## TEAM-DATA-001-REQ-06 추적·실행 경계

Spec·ADR·가이드 겸 Plan·영구 Task·원장을 연결하고 검사 결과를 기록한다. 문서 확정을 새 출처 적재 구현·실데이터 매칭/추천 완료로 표시하지 않는다. 기존 다른 작업의 미커밋 변경을 이번 Task의 구현으로 귀속하지 않는다.

### TEAM-DATA-001-AC-06

SDD 구조와 이번 변경 scope/AC 연결이 검증되고 전체 환경/브랜치 검사의 실행 결과와 기존 작업으로 인한 제한이 구분된다.

## 관련 문서

[ADR-008](../adr/ADR-008-team-collection-contract.md), [가이드·Plan](../team-data-contract.md), [Task](../tasks/team-data-contract.md), [검증](../team-data-contract-validation-20261013.md), [CANONICAL-001](13_canonical_integration_spec.md), [STATS-001](14_statistics_storage_spec.md), [COLLECT-001](../../../../docs/specs/data_collection_record_spec.md).

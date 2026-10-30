# Facility submission preflight — BENCH-FACILITY-001

```toml
kind = "spec"
id = "FACILITY-PACKAGE-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-30"
approval_ref = "현재 대화: BENCH-FACILITY-001 AC01~06 오프라인 시설 제출 패키지 검증기 구현·실측·Objective 중복 제거 비교 요청"
```

## 고정 과제와 인터페이스

난이도 M, 원본 benchmark item은 `BENCH-FACILITY-001` 하나다. 기준 계약은
[TEAM-DATA-001](16_team_collection_schema_spec.md)과 [팀 제출 계약](../team-data-contract.md).
기존 거래·통계 importer와 별도이며 파일·폴더를 읽기만 한다. 수집, 네트워크, 좌표 변환,
매칭, DB 적재, Snowflake, 업로드는 범위 밖이다. 제출 계약 통과는 데이터 사실·사용권·추천
적격성 승인과 다르다. 구현은 stdlib만 사용한다.

`budongi.team_package.validate_package(package_root: Path | str) -> dict` 및
`python -m budongi.team_package PACKAGE_ROOT`를 제공한다. CLI는 JSON 한 개를 stdout으로
출력하고 valid면0, 잘못된 패키지면2를 반환한다. 보고서는 시간/절대경로/예외 원문을 넣지 않는다.

```json
{"schema_version":"team_collection_validation_v1","record_type":"facility",
 "valid":true,"counts":{"raw":2,"accepted":1,"excluded":0,"rejected":1},"errors":[]}
```

오류는 `{"file":"normalized/facility.jsonl","row":2,"field":"name","reason":"required"}`
형식이다. row는 레코드의1-based 위치이며 파일 전체 오류는 null이다. field는 필드 경로,
reason은 고정 코드다. report는 정확히 schema_version/record_type/valid/counts/errors 키를
제공한다. 오류는 `(file,row 또는0,field,reason)` 순 정렬한다. offending value를 반사하지 않는다.

## FACILITY-PACKAGE-001-REQ-01 manifest 메타데이터

manifest.json은 JSON object이며 delivery_schema_version=`team_collection_v1`이다.
다음 명명은 기존 서술 계약을 이번 bounded validator에서 기계화한 것이다.

- 필수 nonempty string: source_id, dataset_id, provider, documentation_url, batch_id,
  mapping_version, collector(담당자), record_url, approval_ref.
- license_ref 또는 license_text 중 nonempty string 하나, 그리고 license_review_status
  (`pending/verified/rejected`)가 필요하다. license 판정 자체를 수락 권한으로 승격하지 않는다.
- scope object에 regions/period/filters 키가 필요하다(미확인 값은 null로 명시 가능).
- source_retrieved_at_utc/provided_at_utc/staged_at_utc 키는 필수이며 null 또는 유효한 UTC Z 시각.
  snapshot_date는 선택이며 null 또는 유효한 YYYY-MM-DD다.
- quality_status는 source_unverified 또는 synthetic_only. files/requests/missing_fields/errors/
  source_missing_dates는 array이며 필수, counts는 아래4개 정수의 object다.
- requests의 각 항목은 collection_status(complete/complete_zero/partial/failed/not_collected),
  expected_rows(null 또는 nonnegative integer), received_rows(nonnegative integer)를 가진다.
  complete_zero의 received_rows는0이다. 실제 수집·커버리지 확인을 외부에 조회하지 않는다.

document/record URL은 http/https 구조를 검사하며 credential-bearing query 이름(api_key,
serviceKey, token, authorization, access_token 등)이나 URL userinfo를 거부한다. URL은 열지 않는다.
잘못된 JSON, 타입, 버전, 누락은 구조화 오류이며 traceback을 출력하지 않는다.

### FACILITY-PACKAGE-001-AC-01

필수 메타데이터/타입·버전·nullable 시각·라이선스 미확인 상태를 검사한다. null을 현재 시각이나
임의 값으로 채우지 않고, missing과 explicit null을 구별한다.

## FACILITY-PACKAGE-001-REQ-02 파일 무결성·안전

files 각 항목은 path/format/bytes/sha256/section/rows를 가진다. path는 root 상대 POSIX 경로,
bytes는 nonnegative integer(bool 금지), sha256은 소문자64 hex, section은 nonempty string이다.
파일 중복, absolute/drive/backslash/.. 경로, symlink 또는 root 밖 참조를 거부하고 읽지 않는다.
원본 bytes SHA/크기를 모든 참조 파일에서 대조한다. raw/와 normalized/ 파일이 각각 필요하다.

첫 구현에서 행 대사가 가능한 형식은 UTF-8 CSV와 JSONL이다. CSV는 header 제외 행 수,
JSONL은 빈 줄 제외 레코드 수를 센다. JSONL은 각 nonempty line이 object여야 한다.
원본 CSV 셀은 문자열로 보존한다. metadata 파일 format=json/text는 rows=null이면 hash/bytes만
검사한다. 그 외 형식이나 알 수 없는 행 수는 unsupported_format/invalid_rows 오류이며 추정하지 않는다.
manifest의 자기 hash는 요구하지 않는다. 정상 package의 raw와 normalized는 한 원본 행당
한 normalized 행을 가지는 `facility_all_status_rows_v1` 한정 프로파일이다. 이 제약은 전체
team_collection_v1의 규칙이 아니다. validation.json에만 rejected 위치를 둔 다른 합법 제출
레이아웃은 첫 구현 미지원(unsupported_layout)으로 구분하며 거부 행을0으로 만들지 않는다.
이 레이아웃 판별은 선택 validation.json의 nonempty rejected 배열과 정규화 rejected 행 부재를
기준으로 하며 counts.rejected는 null로 남긴다. 이 파일의 전체 의미 검증/적재는 하지 않는다.
schema/validation의 전체 JSON Schema 의미 검증은
이6개 AC 밖이며, 기존 원본·다른 도메인을 변환하지 않는다.

### FACILITY-PACKAGE-001-AC-02

hash/크기/행 수 변경, 누락·중복·탈출 경로를 잡으며 원본을 수정하지 않는다.

## FACILITY-PACKAGE-001-REQ-03 facility 레코드

모든 normalized CSV/JSONL 레코드는 name/facility_type_code의 nonempty text와
entity_level=`facility`를 갖는다. excluded/rejected에도 원본 위치와 최소 시설 필드는 보존한다.
시설 코드의 선행0은 보존하며 미등록 분류를 임의 표준 분류로 바꾸지 않는다.

공통 필수: delivery_schema_version/source_id/batch_id/mapping_version/record_type/quality_status,
source_file_ref/source_content_sha256/source_section/source_row_number,
validation_status/validation_reason 키. 동일 배치의 공통 metadata는 record 우선,
schema.json.defaults 다음, manifest 최상위 값 순으로 해석한다. record_type은 facility다.
명시한 source_id/batch_id/mapping_version/버전은 manifest와 일치해야 한다. schema.json은 있으면
object로 읽으며 defaults는 object여야 한다. schema file의 별도 JSON Schema 실행은 하지 않는다.

source_file_ref는 manifest에 등록한 raw 파일이고 source_content_sha256은 그 실제 hash와
일치한다. source_section은 nonempty, source_row_number는 positive integer(bool 금지)다.
CSV의 정수 위치는 decimal digit 문자열로 해석하며 소수/bool형 문자열은 허용하지 않는다.
validation_status는 accepted/excluded/rejected이며 excluded/rejected는 nonempty reason 필수다.
accepted의 reason은 null/빈 문자열이어도 된다. 공식 source_entity_id와 identifier_namespace는
둘 다 비어 있거나 둘 다 nonempty text다. 내부 단지 ID를 생성하지 않는다.

선택 latitude/longitude는 둘 다 null/빈 CSV 셀이거나 둘 다 유한 수이고 -90~90/-180~180다.
bool, NaN/Infinity, 한 쪽만 제공은 오류다. 좌표를 변환·보충·검수 승격하지 않는다.

### FACILITY-PACKAGE-001-AC-03

필수·타입·계보·상태·조건부 ID/좌표를 검사한다. manifest/schema 상속과 명시 값의 충돌을
다르게 처리하며, synthetic_only를 실제 검수 완료로 바꾸지 않는다.

## FACILITY-PACKAGE-001-REQ-04 건수 대사

counts.raw/accepted/excluded/rejected는 모두 nonnegative integer다. raw 파일의 실제 행 합과
정규화 실제 행 수, 상태별 건수, manifest counts를 대사한다. raw=accepted+excluded+rejected다.
알 수 없는 상태·파싱 실패를 rejected나0으로 조용히 치환하지 않는다. 읽을 수 없는 파일은
알 수 없는 수치를 null로 보고하고 invalid다. error가 있어도 읽을 수 있는 다른 파일 검사는 계속한다.

### FACILITY-PACKAGE-001-AC-04

총수/상태별 수/파일별 수 불일치와 bool·음수 건수를 탐지하고 정상0건은0으로 보존한다.

## FACILITY-PACKAGE-001-REQ-05 진단

누락·타입 오류는 required/invalid_type/invalid_value, 위치 오류는 unsafe_path/file_missing,
파일 대사는 sha256_mismatch/bytes_mismatch/rows_mismatch, 건수는 counts_mismatch,
JSON/CSV 파싱은 invalid_json/invalid_csv, 비지원 형식은 unsupported_format 코드를 사용한다.
레코드의 manifest 충돌·계보 불일치는 metadata_mismatch/provenance_mismatch다.
namespace/좌표 규칙 위반은 invalid_value다. 다른 정적 코드 추가는 허용하지만 위 오류는
해당 필수 코드를 포함해야 한다. 민감한 raw value/예외·절대경로는 보고서에 넣지 않는다.

### FACILITY-PACKAGE-001-AC-05

각 문제에 상대 파일·행·필드·고정 사유를 제공하며, 독립 고정 fixture가 이를 판정한다.

## FACILITY-PACKAGE-001-REQ-06 결정성과 read-only

같은 bytes/명세는 같은 dict/JSON을 반환한다. 파싱·대사 실패에도 파일·폴더 생성/수정/삭제,
네트워크/DB/키 접근을 하지 않는다. API와 CLI의 결과는 같다. 판정 시각·루트 절대경로가
출력에 섞이지 않는다. 검증 중 바뀐 파일에 대한 일관성 보장은 별도이며 수집 실행은 하지 않는다.

### FACILITY-PACKAGE-001-AC-06

반복 결과와 전후 전체 파일 bytes hash, CLI/API 출력을 비교한다. 합성 package가 통과해도
실제 시설 자료의 적재/품질/매칭 완료라 보고하지 않는다.

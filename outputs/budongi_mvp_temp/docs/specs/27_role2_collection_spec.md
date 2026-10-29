# ROLE2-COLLECT-001 — 2번(재난·대중교통·생활 인프라) 수집·패키징·메타데이터

```toml
kind = "spec"
id = "ROLE2-COLLECT-001"
status = "approved"
owner = "cannedJean"
revision = 1
approved_by = "사용자"
approved_at = "2026-10-29"
approval_ref = "2026-10-29: 3인 분담안 중 2번을 수행해 팀원과 같은 team_collection_v1 패키지·4시트 메타데이터를 만들고 수집 하네스를 계획하라는 요청과 계획 승인(키 3종 사용, #40·#41 참조만, 정적 우선+소량 실시간 샘플, Issue·Drive는 초안만, 담당 cannedJean·접두어 T, Claude Code 중심+agy 아웃소싱·GMS 제외, 공공누리3·4·비영리는 원본+메타만 공유, HTTP 전용 키 허용 후 재발급)"
```

## 목표·범위·제외 범위

[TEAM-DATA-001](16_team_collection_schema_spec.md)의 2번 역할(교통·상권·환경·공간 레코드)을 실제로 수집한다. 산출물은 배치별 team_collection_v1 ZIP, `cannedJean_수집데이터_메타데이터_YYYYMMDD.xlsx`(4시트), 배치별 COLLECT-001 Issue 초안이다. 수집 런타임·패키저·프로파일러·워크북 작성기는 `budongi.team_collection` 패키지로 새로 만든다.

제외: 좌표 변환 확정·지오코딩·단지 매칭·추천/serving 연결·canonical/통계 DB 적재·GitHub 자동 게시·Drive 자동 업로드·push/merge. 이미 다른 담당이 수집한 #40(OA-394)·#41(15099316)은 재수집하지 않는다. 기존 `source_registry.json`·MOLIT 수집기·managed harness의 동작은 바꾸지 않는다.

## ROLE2-COLLECT-001-REQ-01 출처 등록과 실행 게이트

`team_collection/role2_sources.json`에 출처별 source_id·dataset_id·레인·record_type·라이선스·승인 근거를 등록한다. 수집기는 approved 출처만, 배치에 GitHub `[수집]` Issue URL(`record_url`)과 `approval_ref`가 묶인 경우에만 네트워크를 연다. HTTP 전용 엔드포인트는 레지스트리의 `http_key_exposure_ack`가 있어야 호출한다. 모르는 출처·누락 승인은 네트워크 전에 오류 코드로 거부한다.

### ROLE2-COLLECT-001-AC-01

미등록·미승인·record_url 없음·HTTP 미확인 요청이 네트워크 호출 없이 거부되고, 승인된 배치만 계획(plan)을 만든다는 것이 테스트로 확인된다.

## ROLE2-COLLECT-001-REQ-02 재개 가능한 병렬 수집 런타임

요청 저널은 바이트보다 먼저 시도 기록(sha256·크기)을 남기고, 중단 후 재실행 시 완료 요청은 재호출하지 않는다. origin별 토큰버킷+AIMD와 키·서비스·KST일 기준 쿼터 원장(95%에서 정지, 일일한도 코드 시 다음 날까지 차단)을 적용한다. 요청 상태는 complete·complete_zero·partial·failed·not_collected·inconsistent이며 배치는 모든 요청이 complete/complete_zero일 때만 complete다.

### ROLE2-COLLECT-001-AC-02

가짜 opener로 중단·재개, 해시 불일치 정지, 쿼터 소진·이월, 0건과 실패 구분, 총계 변동 시 inconsistent가 네트워크 없이 검증된다.

## ROLE2-COLLECT-001-REQ-03 자격증명과 비밀 보호

키는 CRED-001 보관함의 명시적 credential ID로 수집 프로세스 안에서만 읽는다. 키는 저널·로그·manifest·ZIP·모델 프롬프트에 남기지 않으며 환경 프록시를 사용하지 않는다. 응답에 키가 반사되면 저장하지 않고 차단한다. 패키지 완성 전 비밀 스윕(원형·URL 인코딩·인용 형태 정확 대조와 패턴 검사)이 0건이어야 한다.

### ROLE2-COLLECT-001-AC-03

가짜 키로 저널·오류 메시지·manifest·ZIP 엔트리에 키가 없음을 확인하고, 반사 응답 차단과 비밀 스윕 실패 시 패키징 중단이 테스트된다.

## ROLE2-COLLECT-001-REQ-04 정규화 레코드

facility·transit_route·transit_stop_link·time_observation·spatial_layer·regional_statistic을 TEAM-DATA-001 envelope로 정규화한다. 모든 `*_utc`는 `…Z` 형식이다. 위경도는 EPSG:4326 근거·축 명시·유한·범위 조건을 모두 만족할 때만 채우고 그 외에는 NULL과 사유, 원 좌표·CRS 후보를 보존한다. 빈 행·서울 외 행은 excluded, 형식 오류 행은 rejected로 원 셀을 보존한다. 같은 입력 서명의 재실행은 신규 0건, 다른 입력의 같은 배치는 오류다.

### ROLE2-COLLECT-001-AC-04

record_type별 필수 필드·사유 코드·좌표 규칙·시각 형식·재실행 결정성이 합성 픽스처로 검증된다.

## ROLE2-COLLECT-001-REQ-05 패키지와 대사

ZIP 하나에는 record_type 하나와 manifest 하나, 정규화 JSONL 하나(accepted+rejected)를 담고 excluded는 `validation/excluded.csv.gz`로 센다. raw·schema·manifest·validation·README·collection·code를 포함하고 파일명 규칙 `출처_종류_지역_조회기간_수집일_배치ID.zip`을 따른다. 결과 본문 전 12개 게이트(행 대사, 파일 참조·해시, 위치 유일성, SHP 개수, 좌표 규칙, 헤더 커버리지, ZIP 안전성, 결정성, 비밀 스윕 등)를 통과해야 한다. 95MB 이상은 조각과 parts.json으로 나눈다. 공공누리3·4·비영리 출처의 공유 ZIP에는 정규화 JSONL을 넣지 않는다.

### ROLE2-COLLECT-001-AC-05

합성 패키지가 게이트를 통과하고, 고의로 깨뜨린 행 수·해시·경로·중복 manifest·좌표가 각각 거부되며, 같은 입력에서 바이트 단위로 같은 ZIP이 만들어진다.

## ROLE2-COLLECT-001-REQ-06 메타데이터 워크북

팀원 양식(제목 2행·메모 3행·헤더 5행·데이터 6행, 데이터셋 목록 29열·컬럼별 메타데이터 30열·데이터 품질 및 연계 29열·전처리 및 이슈 관리 11열, 표 MetadataTable1..4, 틀 고정 C6)으로 작성한다. 비율 셀은 참조 워크북과 같은 수식이며 캐시값을 함께 저장한다. 수치는 결정적 프로파일러만 계산하고, 서술 셀은 공식 문서 근거 게이트를 통과한 문장 또는 고정 문구만 쓴다.

### ROLE2-COLLECT-001-AC-06

합성 워크북의 헤더·수식 문자열·캐시값·틀 고정·표 범위가 독립 판독기와 openpyxl 재읽기로 일치한다.

## ROLE2-COLLECT-001-REQ-07 실제 수집 실행과 기록

출처별 배치를 COLLECT-001 절차(예약 → 재검색 → 수집 → 결과·최종 ZIP SHA-256 기록 → 승인 후 업로드 → 파일 링크)로 실행한다. Claude는 Issue 본문과 사전채움 URL만 만들고 게시·업로드는 사용자가 한다. 실제 성공·0건·실패·미수집 범위와 건수를 검증 문서에 남긴다.

### ROLE2-COLLECT-001-AC-07

검증 문서에 배치별 Issue 번호·상태·건수·ZIP 이름·SHA-256·검사기 일치 결과가 기록되고, 업로드된 배치는 파일 링크가 기록된다.

## ROLE2-COLLECT-001-REQ-08 다중 LLM 작업과 교차검증

코드 유닛은 agy-outsource/agy-delegate와 Claude 계약자로 만들고, 생산자·감사자·심판의 모델 계열을 실제 모델 slug로 분리한다(Opus 계약자 금지, 감사·심판은 계약자와 다른 계열). 리뷰·매핑·서술 판정은 다른 벤더가 블라인드로 수행하고 판정 원장에 해시 체인으로 남긴다. 어떤 모델에도 키·원본·DB·로그·.env를 보내지 않으며 GMS는 사용하지 않는다.

### ROLE2-COLLECT-001-AC-08

검증 문서에 유닛별 생산자·감사자·심판 모델, role_guard 위반 0건, 판정 원장 요약(데이터 없는 집계)이 기록된다.

## 검증 명령과 결과

| AC | 방법 | 상태 |
|---|---|---|
| AC-01~06 | `.venv\Scripts\python.exe -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests -v` (네트워크 없음) | not_run |
| AC-07~08 | [검증 문서](../role2-collection-validation-20261029.md) 기록 | not_run |
| 전체 | `python -X utf8 scripts/check_sdd.py --base origin/main`, `python -X utf8 scripts/verify_environment.py` | not_run |

완료 기록의 원본은 [TASK-ROLE2-HARNESS-001](../tasks/role2-collection-harness.md)과 [TASK-ROLE2-COLLECT-001](../tasks/role2-collection-run.md)이다.

## 관련 문서와 미결정 사항

[ADR-025](../adr/ADR-025-role2-collection-harness.md), [Plan](../plans/role2-collection.md), [TEAM-DATA-001](16_team_collection_schema_spec.md), [팀 데이터 계약](../team-data-contract.md), [COLLECT-001](../../../../docs/specs/data_collection_record_spec.md), [CRED-001](11_api_credential_vault_spec.md).

미결정: 승하차·시간표·상권 집계의 record_type(팀에 transit_schedule·station_statistic 개정 제안, 결정 전 raw-only), 공공누리3·4 출처 정리본의 공유 가능 여부, 좌표 변환과 단지 연결 기준.

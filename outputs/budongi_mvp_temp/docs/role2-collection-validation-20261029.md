# 2번(재난·대중교통·생활 인프라) 수집 검증 기록 — 2026-10-29

[ROLE2-COLLECT-001](specs/27_role2_collection_spec.md)의 실행 증거 원본이다. 원본·키·DB·로그는 넣지 않고 결과 요약과 실행 버전만 기록한다. 아직 실행하지 않은 항목은 not_run으로 둔다.

## 검증 상태

| 항목 | 상태 |
|---|---|
| S0 준비(브랜치·venv·agy) | passed |
| AC-01~06 단위 테스트 | not_run |
| AC-07 수집 배치 기록 | in_progress(raw 10배치, 패키징 전) |
| AC-08 다중 LLM 검증 기록 | in_progress(감사 44/44 Sonnet pass, **채택 44/44**, 전 유닛 실모델 확인·R1 위반 0) |
| SDD·전체 환경 검사 | not_run |

## s0 준비

- 2026-10-29 13:09 KST, 브랜치 `codex/role2-collection-20261029`(main `a7b1714` 기준).
- `.venv`: Python 3.12.10, `pip install -e outputs/budongi_mvp_temp` → openpyxl 3.1.5, cryptography 50.0.2.
- agy 1.4.9 headless preflight: `SUCCESS`(응답 `OK`).
- 팀원 참조 패키지 1개 형상 확인(계획 승인 범위): `STD_전국도서관_전국_20261014_20261014_std-library-national-20261014-v1.zip`, 629,818 B, SHA-256 `1e15a13cbcc153a6332cbc3288ff18ebcfdaf4262951551afedd9f8f66a46dbb`(Issue #14 기록값과 일치), ZIP CRC 정상. manifest·schema·validation·JSONL envelope 키를 role2 패키지 형상의 기준으로 사용한다.

- 2026-10-29 13:27 KST agy gemini-3.8-flash 잡일 2건이 할당량 소진(`Individual quota reached … Resets in 49m`)으로 시작 전에 실패했다. 리셋 후 `role_guard delegate`로 재실행했다. 모든 outsource 계획의 감사자를 Haiku로 통일해 계약자를 Gemini↔claude:sonnet로 바꿔도 R2가 유지되게 했다.
- importer oracle 실측: 고정 importer(blob `f84e2010`)로 팀원 도서관 패키지를 검증해 accepted 3,597·integrity ok, PACKAGES 줄이 원본 `library.zip` 항목과 일치. 팀원 ZIP은 한글 이름을 UTF-8 플래그 없이 저장하므로 오라클이 이름을 재해석한다(role2 raw 파일명은 ASCII).

## ac-01-06 단위 테스트

진행 중. `.venv\Scripts\python.exe -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests/team_collection_tests -t outputs/budongi_mvp_temp/tests` → 2026-10-30 12:00 기준 **195 tests OK**: W0 15개 + 리드 셸 28개(transport·stage·supervisor·package_build·profile_run, 주입식 fake 기반) + 통합 유닛 공개 테스트 152개. `python -m unittest tests.test_role2_harness` → 6 tests OK(role_guard R1~R5 + R2 waiver, importer oracle). r2-core 10유닛·r2-adapt 6유닛을 `integrate --dry-run` 확인 후 제품 트리에 통합(compileall 통과, 커밋 로컬). 숨김 테스트는 run 디렉터리에 봉인 유지.

## ac-07 수집 배치 기록

- 2026-10-29: 사용자 지시로 `gh`(계정 cannedJean)를 사용해 1차 웨이브 예약 Issue #42~#63(22건)을 게시했다. 게시 전후로 공개 API를 재검색했고 겹치는 범위는 없었다(최대 번호 41 → 63).
- 키 없는 파일 출처 10개 배치를 원본 수집했다. 상태: raw 완료, 패키징 전. 요청 49건 complete, 685.8MB.

| T | 배치 디렉터리 | Issue | 원본 |
|---|---|---|---|
| T001 | T001-1 | #46 | 전체_도시철도역사정보_20260630.xlsx 1개 |
| T002 | T002-1 | #47 | 9호선 2-3단계 좌표 CSV(20260131) 1개 |
| T004 | T004-1 | #49 | 침수흔적도 연도별 ZIP 14개, 6.5MB |
| T005 | T005-1 | #50 | 버스정류소 XLSX(20260902)와 컬럼정의 |
| T006 | T006-1 | #51 | 노선별정류소 XLSX(20260902), 3.3MB |
| T007 | T007-1 | #52 | 노선ID XLSX(20260902)와 컬럼정의 |
| T011 | T011-1 | #55 | AIR_HOUR 2020~2022 CSV, 115.4MB |
| R1 | R1-1 | #43 | 생활인구 ZIP 202508~202607 12개, 542.9MB |
| R2 | R2-1 | #44 | 승하차 CSV 202510~202609 12개, 14.5MB |
| T021 | T021-1 | #63 | 상권영역 ZIP 1개, 2.1MB |

- 나머지 12건(#42, #45, #48, #53, #54, #56~#62)은 예약 상태다. 서울 API·data.go.kr 키 레인 코드, 상가정보 POST(10/31 신판), 표준데이터 JSON 페이징이 준비되면 수집한다.

## ac-08 다중 llm 검증 기록

진행 중. 유닛별 생산자·감사자·심판 모델, role_guard 위반 수, 판정 원장 요약을 기록한다.

- 2026-10-29 사용자 지시("감사 계획은 haiku 보다 더 좋은 모델을 사용해야해")로 5개 계획 38유닛 전부를 Sonnet(`claude-sonnet-5-5`)으로 재감사해 모두 pass. 위 S0 메모의 "감사자 Haiku 통일"은 이 결정으로 대체됐고 Haiku는 심판(triage)만 맡는다. Fable은 usage credits가 필요해 쓰지 않았고 r2-hard 계약자는 agy gemini-3.8-flash(effort high)로 바꿨다.
- 감사 지적 반영: contract.py 상수값·ContractError 메시지·base dataclass를 전 계획 conventions에 명시, C1 T-ID 예시 수정, C10 튜플 명시, P4 VALUE_TYPES/STATUSES 추가, H8 `missing()` 호출 횟수 규칙, P3 수동 규칙 번호 제거, E1 재감사 통과.
- 2026-10-29 19:06~10-30 09:20 구현(agy gemini-3.8-flash): 채택 20/38(core 10/10 통합 passed, edge 5/6, xcheck 1/3, pack 3/11, hard 미시작). `role_guard verify-run` 결과 xcheck·core·edge 위반 0·모델 미확인 0.
- 미채택 X1·E2·P3·P5·P6은 agy가 산출물을 쓰고 `DONE`을 출력한 뒤 프로세스가 종료되지 않은 경우였다(30분 timeout 3건, 밤사이 약 12시간 멈춤 2건). 2026-10-30 09:20 실행을 중지하고 이 작업의 프로세스만 종료, 숨김 테스트 평문 사본 0건을 확인했다. 재개 절차는 [인계 기록](role2-handoff-20261030.md#4-외주-빌드-상태2026-10-30-0920-중지-시점)을 따른다.
- 2026-10-30 09:36 r2-pack을 gemini(`--timeout 15`, `-j 4`)로 재개: P3·P5·P6이 같은 미종료 문제로 다시 timeout 소진(15분), P2는 forbid 게이트 실패 후 2차 시도. 접합부 문제가 재현되어 10:04 실행을 중지했다(이 작업 프로세스만 종료).
- 2026-10-30 사용자 지시로 agy 계약자를 `agy:claude-sonnet-5-5`(effort 기본 high)로 전환. 전 계획 감사자가 Sonnet이라 R2와 충돌 → `role_guard.py`에 기록형 waiver(`--waive-r2-overlap`)를 추가해 "감사자 ≠ 계약자 계열" 절만 사유 명시 시 완화(감사자 Anthropic·비리드·비gemini 핵심은 불변, R1·R3 불변). 근거: [ADR-025 Amendment](adr/ADR-025-role2-collection-harness.md), `python -m unittest tests.test_role2_harness` → 6 tests OK. r2-pack·r2-xcheck·r2-edge·r2-adapt effort를 high로 변경(outsource 감사 해시는 effort를 판정 대상에서 제외).
- 2026-10-30 r2-adapt(어댑터 유닛 E6·E7·E8·E9·E10·E12, WF-0 도시에 기반) 계획 작성: `check --red` 통과, Sonnet 감사 6/6 pass(E9·E10은 1차 지적 → 스펙 보강 → 재감사 pass). 리드 셸 `transport.py` 작성, team_collection 테스트 20개 OK.
- 2026-10-30 10:05~10:59 r2-pack을 `agy:claude-sonnet-5-5`(effort high, `-j 2`, R2 waiver 기록)로 실행: P5·P11·P12 수락(기존 P1·P4·P7 포함 6/11). P2는 3회 전부 forbid 게이트 거부 — 원인은 스펙 필수 식별자 `requests`(manifest 요청 목록 키·시그니처)가 네트워크 금지 단어 패턴에 걸리는 **게이트 오탐**(공개 6·숨김 25 테스트는 통과). P3·P6·P9·P10은 agy 프로세스 잔류로 timeout(sonnet 세션 자체는 39~57초 완료, 잔류는 간헐·벤더 공통, 15분 timeout으로 수습).
- 2026-10-30 11:05~11:58 Claude 미터 소진(리셋 약 4시간) 후 사용자 지시로 gemini flash high 대체: r2-xcheck는 X2 수락 유지·X1 접합부 멈춤 3회째(X1·X3는 sonnet 복귀 후 처리), r2-adapt는 **6/6 수락**(E6~E9·E12 1차, E10 재시도 수락, 통합 테스트 passed), verify-run 두 계획 모두 위반 0·미확인 0. r2-core 10유닛·r2-adapt 6유닛 제품 통합. 매핑 B안(Opus) 8종 초안과 A안용 헤더-only 입력(`mappings_prep/`)을 작성.
- 2026-10-30 12:06~12:35 r2-pack 잔여를 gemini high로 완주: **11/11 수락**(P9·P10·P11은 게이트 피드백 2차 수락, P6·P12 재시도 수락), r2-core·r2-adapt·r2-pack 3계획 27유닛 제품 통합 — 스위트 290 tests OK.
- 2026-10-30 12:38~13:10 필드 매핑 A/B(§6-4): Gemini A안(값 없는 헤더 형상만 입력, confined delegate) + Opus B안 8종 독립 작성 → `diff_ab.py` 결정적 비교(1차에서 B안의 T001 헤더 누락 3열과 T004 변형 분할 필요를 발견해 수정) → 충돌 84건을 익명·해시 정렬 패킷으로 Sonnet 블라인드 심판(`tooling/role2_harness/review_packet.py` 신규 구현: 저장소 밖·tools 차단·check_ran_as·원장 기록) → `apply_verdicts.py`로 결정적 반영. 미합의 9건(한쪽만 매핑 유형)은 unmapped+T-I 이슈로 분류: T001 부가 5열(영문·한자 역사명, 환승 3열), T004 2023·2024의 GU_NAM(실파일에 없는 열 — A안 오류, 결정적 제외), T006 좌표 2열(T005 보유).
- 2026-10-30 13:40~14:00 매핑 동결: 수락된 H1 compile_mapping으로 **11개 매핑 전부 compile 통과**, 실제 헤더 집합 26개 전부 coverage complete. 2022 침수흔적도 dbf(76MB, 프로브 상한 초과로 형상 누락)는 스트림 헤더 판독으로 18열 확인 후 **schema_2022 변형을 기판정 필드만 재사용해 추가**(OBJECTID·layer·path는 unmapped+T-I; T004는 총 5변형, 14개 연도 파일이 각각 정확히 1개 변형에 매칭). 최종 매핑 8파일을 `src/budongi/team_collection/mappings/`로 동결(pyproject package-data 기포함).
- 2026-10-30 13:42~14:25 r2-hard 완주: gemini high로 H1·H2·H3·H6·H8(1차)·H4·H7(재시도) 수락, 마지막 H5는 자원 사다리(사용자 지시)로 **claude 측 미터(claude:sonnet 계약자, R2 waiver 기록)**에서 1차 수락 — **r2-hard 8/8, 통합 테스트 passed**. 제품 통합 후 스위트 **337 tests OK**. 참고: H6·H8 프로파일러가 gemini 작성으로 확정되어 X1·X3을 claude:sonnet으로 돌리는 것이 교차벤더에 부합(X2 recount만 프로파일러와 동일 gemini — Opus 숨김 테스트·data_only 재읽기·Excel COM 재계산이 견제, 기록으로 관리).
- 2026-10-30 14:40~14:55 외주 빌드 종료: X1·X3·E2가 claude:sonnet 1차 수락으로 **6계획 44/44 유닛 전부 수락·제품 통합**, 스위트 **401 tests OK**. 실제 계약자 계열 집계(attempt 기록 기준): gemini 35·sonnet 9, 리드 계열(Opus) 위반 0, 모델 미확인 0. 계획별: core 10 gemini / edge 5 gemini+1 sonnet / adapt 6 gemini / pack 6 gemini+5 sonnet / xcheck 1 gemini+2 sonnet / hard 7 gemini+1 sonnet. R2 중첩 waiver가 적용된 실행은 실행 로그에 사유 JSON으로 기록됨.
- 2026-10-30 14:30 wiring(조립 모듈) 스모크: T001 실헤더 변형 선택·주소 접두사 scope·매핑 적용 0오류·facility 정규화·4326 근거 좌표 표준화(lat/lon 채움, review pending)까지 통과. 이 과정에서 심판이 고른 `facility_type_code=rail_station`이 계약 §5의 명시 어휘와 달라 **계약 우선 원칙으로 `transit.subway_station`으로 결정적 교정**(T001·T002, 투표는 계약을 뒤집지 못함). 식별자 네임스페이스는 T005~T007 교차 참조 일관성 확인 후 심판 선택 유지. r2-pack·r2-hard·r2-adapt에서 `requests` 단어 매칭을 import/호출 형태 매칭 2건으로 교체(라이브러리 import 차단은 imports 게이트가 별도 수행, urllib·socket·subprocess 단어 차단 유지). 게이트 변경으로 r2-pack은 수락분 포함 전체 재검증 실행. 수정이 불필요한 r2-edge·r2-xcheck는 원본 패턴으로 원복해 기존 수락 6유닛(E1·E3·E4·E5·E11·X2)의 상태를 보존(r2-core와 패턴 일치 확인).

## 파일럿 패키징 (2026-10-30 14:10~14:50)

- cli에 `stage`·`package` 명령을 와이어링(동결 매핑+staging_config+실유닛 조립). T001 스테이징: raw 1,099 → accepted 336(서울)·excluded 757(비서울)·rejected 6. 거부 6건은 전부 서울 역사로, 원본의 **달력상 불가능한 1900년대 기준일자**(형식은 Y-M-D이나 실존하지 않는 날짜) 때문 — 계약상 invalid_date 거부가 맞고 원문은 `base_date_raw`로 보존(T-I 이슈로 Issue 본문에 기재 예정). T002: 13/13 accepted(언주~중앙보훈병원 13개 역 일치).
- 보강 2건: ① 보관함 조회는 명시 credential ID만 사용(expected_provider 메타 대조 제거 — CRED-001의 명시 바인딩 원칙), ② manifest files[] 항목에 팀 참조 패키지 형상대로 format/rows(raw는 encoding·section 포함) 추가.
- **리드 스펙 버그 수정**: H5 selfcheck가 counts 키를 `raw`로 기대했으나 팀 계약·참조 패키지는 `raw_rows` — H5 스펙·공개/숨김 테스트 수정 → Sonnet 재감사 pass → claude:sonnet 재실행 1차 수락 → 재통합(스위트 401 OK 유지).
- **T001 패키지**: `KRIC_도시철도역사_전국_20260630_20261029_kric-urban-rail-station-std-20261029-v1.zip` 356,015B, SHA `abb65bd2…832cc8`. 게이트: 빌더 대사·record_check·비밀 스윕(보관함 키 3종 실조회 대조) 통과, **이중 빌드 SHA 동일**(게이트 11), selfcheck ok·errors 0, **고정 blob importer oracle ok**(accepted 336·rejected 6·integrity ok), X2 독립 recount 342 일치·full dup 0. **검사기 4종 완전 일치.**
- **T002 패키지**: `서울교통공사_9호선역좌표_서울_20260131_20261029_….zip` 10,869B, SHA `6247004a…c448a2`. selfcheck ok, importer oracle accepted 13·rejected 0·integrity ok.
- **파일럿 go/no-go: GO.** 나머지 배치 패키징으로 진행(Drive 업로드는 배치 목록 사용자 승인 후).

## sdd 검증

not_run. `scripts/check_sdd.py --base origin/main`과 `scripts/verify_environment.py` 결과를 기록한다.

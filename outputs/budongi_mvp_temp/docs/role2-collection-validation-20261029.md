# 2번(재난·대중교통·생활 인프라) 수집 검증 기록 — 2026-10-29

[ROLE2-COLLECT-001](specs/27_role2_collection_spec.md)의 실행 증거 원본이다. 원본·키·DB·로그는 넣지 않고 결과 요약과 실행 버전만 기록한다. 아직 실행하지 않은 항목은 not_run으로 둔다.

## 검증 상태

| 항목 | 상태 |
|---|---|
| S0 준비(브랜치·venv·agy) | passed |
| AC-01~06 단위 테스트 | not_run |
| AC-07 수집 배치 기록 | not_run |
| AC-08 다중 LLM 검증 기록 | not_run |
| SDD·전체 환경 검사 | not_run |

## s0 준비

- 2026-10-29 13:09 KST, 브랜치 `codex/role2-collection-20261029`(main `a7b1714` 기준).
- `.venv`: Python 3.12.10, `pip install -e outputs/budongi_mvp_temp` → openpyxl 3.1.5, cryptography 50.0.2.
- agy 1.4.9 headless preflight: `SUCCESS`(응답 `OK`).
- 팀원 참조 패키지 1개 형상 확인(계획 승인 범위): `STD_전국도서관_전국_20261014_20261014_std-library-national-20261014-v1.zip`, 629,818 B, SHA-256 `1e15a13cbcc153a6332cbc3288ff18ebcfdaf4262951551afedd9f8f66a46dbb`(Issue #14 기록값과 일치), ZIP CRC 정상. manifest·schema·validation·JSONL envelope 키를 role2 패키지 형상의 기준으로 사용한다.

- 2026-10-29 13:27 KST agy gemini-3.8-flash 잡일 2건이 할당량 소진(`Individual quota reached … Resets in 49m`)으로 시작 전에 실패했다. 리셋 후 `role_guard delegate`로 재실행했다. 모든 outsource 계획의 감사자를 Haiku로 통일해 계약자를 Gemini↔claude:sonnet로 바꿔도 R2가 유지되게 했다.
- importer oracle 실측: 고정 importer(blob `f84e2010`)로 팀원 도서관 패키지를 검증해 accepted 3,597·integrity ok, PACKAGES 줄이 원본 `library.zip` 항목과 일치. 팀원 ZIP은 한글 이름을 UTF-8 플래그 없이 저장하므로 오라클이 이름을 재해석한다(role2 raw 파일명은 ASCII).

## ac-01-06 단위 테스트

진행 중(리드 코드만). `.venv\Scripts\python.exe -X utf8 -m unittest discover -s outputs/budongi_mvp_temp/tests/team_collection_tests -t outputs/budongi_mvp_temp/tests` → 15 tests OK(W0 레지스트리 게이트·계획 불변성·파일 저널·복구·잠금, 키 핸들·비밀 스윕·GitHub 검색). `python -m unittest tests.test_role2_harness` → 5 tests OK(role_guard R1~R5, importer oracle). outsource 유닛은 아직 미통합.

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

not_run. 유닛별 생산자·감사자·심판 모델, role_guard 위반 수, 판정 원장 요약을 기록한다.

## sdd 검증

not_run. `scripts/check_sdd.py --base origin/main`과 `scripts/verify_environment.py` 결과를 기록한다.

# ADR-025 — 2번 수집 하네스: 결정적 수집 런타임 + 다중 LLM 빌드·교차검증

Status: Accepted (2026-10-29, 사용자 계획 승인)

| 항목 | 작성 내용 |
| --- | --- |
| ID | ADR-025 |
| 담당자·날짜 | cannedJean (Claude Code Opus 5.5 리드), 2026-10-29 |
| 관련 문서 | [ROLE2-COLLECT-001](../specs/27_role2_collection_spec.md) REQ/AC-01~08, [Plan](../plans/role2-collection.md), [TASK-ROLE2-HARNESS-001](../tasks/role2-collection-harness.md), [TASK-ROLE2-COLLECT-001](../tasks/role2-collection-run.md) |
| 범위·제외 범위 | 2번 출처의 수집·정규화·패키징·메타데이터 작성 구조. 기존 MOLIT 수집기, `python -m harness`, GMS 예산 runner, canonical/통계 DB는 바꾸지 않는다 |

## Context

- 2번 출처는 키 없는 파일, data.go.kr API, 서울 열린데이터 API(HTTP 전용, 1,000행 창), TOPIS 버스 API(HTTP 전용, 서비스당 하루 1,000회), 공간 파일(SHP), WMS 이미지로 형태가 다양하다. 기존 `budongi.collection`은 MOLIT 3개 서비스·구×월 계획에 묶여 있고 직렬이다.
- 기존 managed harness(`python -m harness`)는 저장소당 1작업, 프롬프트가 데이터 수집을 금지하고, 검증은 테스트 명령만 허용하며, 기본 provider인 Codex가 이 PC에 없다. GMS 키는 만료로 기록돼 있고 사용자는 이번 작업에서 GMS를 제외했다.
- team_collection_v1 패키저·프로파일러·4시트 워크북 작성기는 저장소에 없다. 팀 importer(미병합 브랜치 blob `f84e2010`)는 ZIP당 manifest 1개·정규화 JSONL 1개·accepted/rejected만 받는다.
- 사용자는 Claude Code 중심 + agy 아웃소싱, 자기선호 편향을 막는 교차검증, 최대한 빠른 병렬 수집을 요청했다.

## Decision

1. **데이터 평면과 제어 평면 분리.** 키·원본·레코드는 `.venv`의 결정적 Python(`budongi.team_collection`)만 다룬다. 모델은 스펙·코드·테스트·공개 문서·집계만 다룬다.
2. **새 수집 런타임.** 출처 레지스트리(`role2_sources.json`) + 레인별 어댑터 + 요청 저널(바이트 전 기록) + origin별 토큰버킷/AIMD + SQLite 쿼터 원장 + 배치별 `.fetch.lock`. `collection.py`의 원자적 쓰기·안전 경로·반사 키 검사 등은 재사용하고 MOLIT 전용 계획 로직은 복제하지 않는다.
3. **record_type별 ZIP.** importer 호환을 위해 ZIP 하나에 record_type 하나, excluded는 JSONL 밖에서 센다. 12개 게이트와 검사기 4종(빌더·selfcheck·고정 importer·독립 recount)이 일치해야 결과 본문을 만든다.
4. **다중 LLM 빌드.** Opus 리드가 스펙·숨김 테스트·보안 셸·판정을 맡는다. 고난도 유닛은 agy-outsource의 `claude:sonnet` 계약자, 중간·단순 유닛은 agy `gemini-3.8-flash`가 구현한다. `role_guard`가 실제 모델 slug로 생산자·감사자·심판 계열을 분리하고, 리뷰·매핑·서술 판정은 다른 벤더가 블라인드로 수행해 해시 체인 원장에 남긴다.
5. **managed harness·GMS·Codex 미사용.** 위 Context의 제약 때문이며, 이 작업 한정 결정이다.

## Alternatives

- managed harness에 agy/claude provider를 추가해 수집까지 실행: 1작업 직렬·수집 금지 계약·데이터 경로 커밋 거부와 충돌하고 범위가 커서 제외.
- MOLIT `collection.py` 일반화: 기존 975/2,400 query 재현성과 테스트를 흔들 위험이 있어 원시 함수 재사용으로 제한.
- 단일 모델(Opus)만으로 구현: 자기선호 편향 통제와 처리량 요구를 충족하지 못함.
- xlsxwriter·polars·pyproj 추가: CI는 `pip install -e`만 설치하므로 의존성 추가 없이 stdlib+openpyxl로 결정.

## Consequences

- 새 코드는 `outputs/budongi_mvp_temp/src/budongi/team_collection/`, 테스트는 `outputs/budongi_mvp_temp/tests/team_collection_tests/`, 빌드 도구는 `tooling/role2_harness/`에 둔다. 런타임 산출물은 Git 제외 경로에 둔다.
- 서울 열린데이터·TOPIS 키는 HTTP로 전송되므로 사용자 확인을 레지스트리에 기록하고 수집 후 키를 재발급한다.
- 좌표 변환·단지 매칭·DB 적재는 후속 Task다. 승하차·시간표·상권 집계는 계약 개정 전 raw-only다.

## Verification

ROLE2-COLLECT-001-AC-01~06은 unittest, AC-07~08은 [검증 문서](../role2-collection-validation-20261029.md)로 확인한다. 현재 상태 not_run.

## Amendment — 2026-10-30 R2 중첩 예외(기록형)와 계약자 전환

사용자 지시(2026-10-30)로 agy 계약자를 Claude 모델 위주로 전환하면서 역할 규칙을 다음과 같이 유연화했다.

- **배경:** agy gemini-3.8-flash 세션이 산출물과 `DONE`을 쓰고도 종료하지 않는 접합부 문제로 X1·E2·P3·P5·P6이 반복 timeout 됐다(약 12시간 손실 포함). 한편 2026-10-29 "감사는 haiku보다 좋은 모델" 지시로 전 계획 감사자가 Sonnet이어서, 계약자를 `agy:claude-sonnet`으로 바꾸면 R2(감사자 ≠ 계약자 계열)와 충돌했다.
- **판단:** Sonnet 감사 지시 자체는 유지한다. 감사는 계약자 코드가 아니라 **리드(Opus)의 테스트·스펙**을 코드 작성 전에 판정하므로, 감사자의 핵심 독립성은 리드로부터의 독립이다. 실제로 Sonnet 감사가 Haiku가 놓치기 쉬운 스펙 모호성을 잡아낸 기록이 있다(2026-10-29 감사 지적 반영 목록, 2026-10-30 E9·E10). 또한 Fable(claude -p)이 크레딧 문제로 불가한 상황에서 감사를 haiku로 되돌리면 sonnet 계약자 기준 심판(R3) 가용 계열이 없다 — sonnet 감사 유지 + R2 중첩 예외가 유일한 실행 가능 구성이다.
- **변경:** `role_guard.py`의 R2에서 "감사자 ≠ 계약자 계열" 절만 **명시적 사유가 있는 waiver**(`--waive-r2-overlap REASON`)로 완화한다. 감사자가 Anthropic이고 리드 계열·gemini가 아니어야 한다는 핵심은 불변이며, waiver는 실행 로그에 JSON으로 남는다. R1(계약자 ≠ Opus, agy 경유 Opus 금지)과 R3(심판 분리: sonnet 계약자+sonnet 감사 시 심판 haiku)는 그대로다. 근거 테스트: `tests/test_role2_harness.py::test_r2_overlap_waiver_relaxes_only_the_contractor_clause`.
- **운용(2026-10-30 10:30 갱신):** agy 토큰 리셋 후 사용자 지시로 특정 모델 우선은 해제하고 용도 기반으로 라우팅한다. effort 기본 high와 `-j 2`(Claude 미터 한도)는 유지. 구현 계약자는 `agy:claude-sonnet-5-5`(R2 waiver 기록) — gemini는 같은 유닛에서 미종료가 반복된 반면 sonnet은 정상 종료·빠른 수락을 확인(P5 57초). 교차검증 측(X1·X3 readback, X2 recount, 매핑 A안, 리드 셸 적대 테스트, 서술 초안)은 벤더 분리를 위해 gemini flash를 유지한다.

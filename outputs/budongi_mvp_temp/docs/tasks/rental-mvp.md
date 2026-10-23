# TASK-RENT-MVP-001 — 대화형 DB 전월세 추천 MVP

```toml
kind = "task"
id = "TASK-RENT-MVP-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["outputs/budongi_mvp_temp/tests/test_rental_review.py", "outputs/budongi_mvp_temp/scripts/benchmark_rentals.py", "outputs/budongi_mvp_temp/pyproject.toml", "outputs/budongi_mvp_temp/docs/adr/ADR-009-reviewed-rental-serving.md", "outputs/budongi_mvp_temp/docs/specs/00_project_spec.md", "outputs/budongi_mvp_temp/docs/rental-review-package.md", "outputs/budongi_mvp_temp/src/budongi/canonical_rental.py", "outputs/budongi_mvp_temp/src/budongi/rental_review.py", "outputs/budongi_mvp_temp/src/budongi/rental_recommendation.py", "outputs/budongi_mvp_temp/src/budongi/rental_server.py", "outputs/budongi_mvp_temp/src/budongi/cli.py", "outputs/budongi_mvp_temp/src/budongi/static/rental.html", "outputs/budongi_mvp_temp/src/budongi/static/rental.css", "outputs/budongi_mvp_temp/src/budongi/static/rental.js", "outputs/budongi_mvp_temp/src/budongi/static/vendor/leaflet/", "outputs/budongi_mvp_temp/tests/test_canonical_rental.py", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/09_runtime_spec.md", "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md", "outputs/budongi_mvp_temp/docs/tasks/rental-mvp.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/rental-mvp-validation-20261013.md", "outputs/budongi_mvp_temp/README.md", "outputs/budongi_mvp_temp/AGENTS.md", "README.md", "AGENTS.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14", "RENT-001-AC-15"]

[[verification]]
command = "manual: PLAN-RENT-001의 대화·실제 DB·두 상세 페이지·지도·지연 시나리오를 구현 후 검증"
result = "not_run"
evidence = "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md#2026-10-13-mvp-범위-확장-및-실행-계획"
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14", "RENT-001-AC-15"]

[[verification]]
command = "$env:PYTHONPATH='src'; python -m unittest discover -s tests -p 'test_canonical_rental.py' -v; node --check src/budongi/static/rental.js; python -m py_compile src/budongi/canonical_rental.py src/budongi/rental_server.py src/budongi/cli.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/rental-mvp-validation-20261013.md#동작-검증"
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14"]

[[verification]]
command = "실제 canonical serving DB에서 동일한 월세/종로구 조건 5회 워밍업 후 추천 API 함수 100회 계측 및 EXPLAIN QUERY PLAN"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/rental-mvp-validation-20261013.md#실제-db-읽기-지연-및-쿼리-계획"
acs = ["RENT-001-AC-15"]

[[verification]]
command = "번들 Python: PYTHONPATH=src python -m unittest discover -s tests -v"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/rental-mvp-validation-20261013.md#동작-검증"
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14"]

[[verification]]
command = "실제 serving DB로 loopback /, /api/status, POST /api/recommendations 요청; 브라우저에서 검색 후 needs/details 탭 전환"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/rental-mvp-validation-20261013.md#동작-검증"
acs = ["RENT-001-AC-13", "RENT-001-AC-14"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "failed"
evidence = "outputs/budongi_mvp_temp/docs/rental-mvp-validation-20261013.md#남은-검증-게이트"
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14", "RENT-001-AC-15"]

[[verification]]
command = "번들 Python: python -X utf8 scripts/verify_environment.py; node --check outputs/budongi_mvp_temp/src/budongi/static/rental.js"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/rental-mvp-validation-20261013.md#2026-10-14-최종-재검증"
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14", "RENT-001-AC-15"]

[[verification]]
command = "manual: GMS budgeted gms-work --execute 초안 검토·날짜 경계 5개 테스트 실행; 실제/합성 benchmark 5warmup100회; 최신 UI 기본값·확인 전 추천 미조회 검증"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/rental-mvp-validation-20261013.md#2026-10-14-최종-재검증"
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14", "RENT-001-AC-15"]
```

## 목표·범위·확정 근거

2026-10-13 사용자가 승인한 MVP 목표와 [RENT-001 revision 5](../specs/10_rental_recommendation_spec.md), [PLAN-RENT-001](../plans/rental-recommendation-mvp.md)을 구현한다. 채팅에서 로컬 LLM이 누락/모호한 조건을 확인하고, 사용자가 확정한 구조화 조건으로 실제 SQLite 기반 결정적 추천을 실행한다. 니즈 비교 페이지와 전체 DB 상세 페이지를 별도로 제공하고, 검수 좌표가 있을 때 지도에 표시한다. DB 조회 지연 p95 목표는 500ms다.

2026-10-13 사용자가 실제 전월세 **확정 매칭 단지만 추천**하도록 선택했다. 2026-10-13 기준 보존 canonical DB는 실제 전월세 관측 238,620건이지만 `complex_id`가 연결된 전월세는 0건이고 271,299 후보가 모두 `pending`이다. 그러므로 실제 결과는 `data_not_ready`로 표현하고, pending 후보/원본별 관측을 단지 후보로 승격·그룹·병합하지 않는다. 현재 DB에는 좌표와 시설 데이터가 없으므로 위치·시설은 미제공 상태다. 새 출처 수집, 지오코딩, 시설 조회, 후보 자동 확정은 포함하지 않는다. 사용자가 선택한 Leaflet+OSM 배경 타일은 지도 보기 동작에 한해 포함한다.

의존: TASK-RENT-REC-001과 TASK-CANONICAL-001. 보관함 loopback 보안 경계를 재사용한다. 실행 DB 경로는 설정 가능하되 read-only로 연다. synthetic-demo는 명시적으로 선택한 경우에만 사용한다.

2026-10-20 검수 serving `data/rental/serving/reviewed-20261020.sqlite3`에는 238,620건 중 203,159건(5,156개 단지)의 승인 관계가 반영됐다. 예외 35,461건은 미확정이며 연결 거래의 상태도 모두 `unknown`이라 실제 추천은 `data_not_ready`다. 보존한 이전 canonical의 0건 연결과 이 검수 serving을 구분한다.

## 완료 기준

- [ ] RENT-001-AC-12 채팅 추가 질문은 조건을 구조화하고 사용자 확인을 거치며, 모델 장애 때 입력을 보존한다.
- [x] RENT-001-AC-13 실제 canonical DB만 조회하고 source/batch/row provenance가 있는 데이터만 노출한다. 확정 매칭이 0이면 `data_not_ready`를 반환한다. 세부 항목은 등록 필드 카탈로그로 확장한다.
- [x] RENT-001-AC-14 니즈 비교 화면과 전체 상세 화면이 분리되어 있고, verified 좌표만 지도에 표시한다. 좌표 미제공 상태에서 위치를 추정하지 않는다.
- [ ] RENT-001-AC-15 실제 canonical DB를 이용한 반복 계측에서 warmed backend DB read p95 ≤ 500ms를 달성하고 쿼리 계획·계측 결과를 남긴다.

## 검증·결과

T1~T6 코드를 구현하고 전용 20개 테스트와 GMS 초안을 검토한 날짜 경계 5개 테스트·기존 합성 추천 15개·실제 미준비 및 합성 성공/지도 브라우저 흐름을 검증했다. AC-13과 AC-14의 데이터 계약·두 화면/지도 기능을 확인했다. 실모델과 실제 비어 있지 않은 추천·상세 지연은 사용자 답변대로 준비 조건이다. 따라서 Task와 전체 Goal은 in_progress다. 상세 결과·지연·데이터 제한은 [검증 기록](../rental-mvp-validation-20261013.md)을 따른다.

## 2026-10-14 승인 계획 실행

T1 검수 패키지/serving v2 → T2 공통 판정 → T3 대화·확인 → T4 두 화면·Leaflet → T5 회귀·성능 → T6 문서·SDD 순서로 진행한다. 현재 변경 후 검사 결과는 과거 143개 통과 기록으로 대체하지 않는다.

목표 재감사에서 REQ-06의 이전 HTTP 503/웹 TARGET 설명과 프로젝트·현재 Task의 구현 상태를 현재 코드/승인 계약에 맞췄다. 초기 Plan의 지도·대화 제외 표는 초기 승인 이력으로 표시했다. [항목별 감사](../rental-mvp-validation-20261013.md#목표-항목별-완료-감사)와 SDD 재검사(기능12/AC71/Task28/변경64 통과)를 기록했다. 실제 DB 상태와 로컬 모델 설정은 여전히 준비 게이트를 입증하므로 AC-12·AC-15는 미완료로 유지한다.

최신 검증 원본은 [2026-10-14 구현 검증](../rental-mvp-validation-20261013.md#2026-10-14-구현-검증)이다. T1 serving/검수 패키지, T2 공통 판정, T3 대화/확인/복구, T4 니즈/상세/내장 지도, T5 합성·미준비 성능/회귀, T6 문서/원장 구현을 완료했다. 실제 검수 데이터·실모델과 그 성공 경로는 완료하지 않았다.

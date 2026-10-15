# TASK-TEAM-DATA-001 — 수집 전 공통 스키마 확정

```toml
kind = "task"
id = "TASK-TEAM-DATA-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/16_team_collection_schema_spec.md"]
scope = ["outputs/budongi_mvp_temp/docs/team-collection-chat-summary.md", "outputs/budongi_mvp_temp/docs/team-collection-details.md", "outputs/budongi_mvp_temp/docs/specs/16_team_collection_schema_spec.md", "outputs/budongi_mvp_temp/docs/adr/ADR-008-team-collection-contract.md", "outputs/budongi_mvp_temp/docs/team-data-contract.md", "outputs/budongi_mvp_temp/docs/team-data-contract-validation-20261013.md", "outputs/budongi_mvp_temp/docs/tasks/team-data-contract.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["TEAM-DATA-001-AC-01", "TEAM-DATA-001-AC-02", "TEAM-DATA-001-AC-03", "TEAM-DATA-001-AC-04", "TEAM-DATA-001-AC-05", "TEAM-DATA-001-AC-06"]

[[verification]]
command = "프로젝트 venv Python SQLite mode=ro/query_only probe: 실제 DB integrity/FK/건수 및 in-memory SCHEMA/DDL 대조"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/team-data-contract-validation-20261013.md#db-inspection"
acs = ["TEAM-DATA-001-AC-01"]

[[verification]]
command = "첨부 분담안·기존 코드/Spec/ADR 대조: 팀 가이드 §2~8 및 상대 문서 링크 19개 확인"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/team-data-contract-validation-20261013.md#contract-review"
acs = ["TEAM-DATA-001-AC-02", "TEAM-DATA-001-AC-03", "TEAM-DATA-001-AC-04", "TEAM-DATA-001-AC-05"]

[[verification]]
command = "check_sdd.validate(이번 7개 경로) 및 .venv/Scripts/python.exe -X utf8 scripts/check_sdd.py --base origin/main; 전체 환경 검사 실패/제한 기록"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/team-data-contract-validation-20261013.md#sdd-validation"
acs = ["TEAM-DATA-001-AC-06"]
```

## 목표·범위

2026-10-13 사용자의 첨부 3인 분담안을 기존 코드/실제 SQLite와 대조하여 수집 전에 필요한 제출·DB 호환 계약을 확정한다. 새 수집/키/매칭/DB 변경/추천/업로드/PR은 실행하지 않는다. 제품 요구를 확대하지 않으며 미지원 record_type의 수집 후 적재 구현은 별도다.

## 완료 기준

- [x] TEAM-DATA-001-AC-01 실제 DB 구조·건수·무결성과 현재 적재 지원 경계를 대조한다.
- [x] TEAM-DATA-001-AC-02 ID namespace·계층·주소코드·NULL·충돌 규칙을 확정한다.
- [x] TEAM-DATA-001-AC-03 단위·타입·좌표·날짜·결측의 교환 필드 사전을 확정한다.
- [x] TEAM-DATA-001-AC-04 패키지·상태·계보·대사·재실행·기존 어댑터 한계를 정의한다.
- [x] TEAM-DATA-001-AC-05 세 담당의 제출과 수집 후 결정/증거/책임을 구분한다.
- [x] TEAM-DATA-001-AC-06 Spec/ADR/Task/원장·scope 검증과 전체 검사 제한을 기록한다.

## 검증과 남은 조건

[검증 기록](../team-data-contract-validation-20261013.md)이 실제 실행 결과의 원본이다. 이번 완료는 수집 전 문서 계약의 완료이며 새 출처/관계/시설/공간 어댑터 구현이나 실제 추천·품질 완료가 아니다. 현재 DB의 미연결 전월세·pending 후보는 유지한다. 실제 샘플 확보 후 가이드 §8의 결정/후속 Task를 진행한다.

전체 환경 검사에는 기존 폴더 게시 rename 접근 오류 3건이 남아 실패했다. 실제 DB 무결성·스키마 대조와 SDD는 통과했으며, 문서 AC 완료를 전체 제품 회귀 성공으로 표시하지 않는다.

## 2026-10-14 문서 연결 보완

승인된 MVP T6의 전체 SDD 연결 정리로, 기존 팀 가이드를 설명하는 채팅 요약·상세 내역 두 문서를 이 Task 범위에 연결했다. 기존 출처/제출·후속 결정·수집 승인 경계를 설명하는 자료이며 실제 수집·매칭·새 제품 요구를 승인하지 않는다. 두 문서 내용은 보존했다.

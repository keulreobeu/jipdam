# TASK-AUDIT-GMS-001 — 상태 재검증과 개인 키별 GMS 관리

```toml
kind = "task"
id = "TASK-AUDIT-GMS-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/gms_budget.py", "outputs/budongi_mvp_temp/src/budongi/gms_accounts.py", "outputs/budongi_mvp_temp/src/budongi/credential_server.py", "outputs/budongi_mvp_temp/src/budongi/static/credentials.js", "outputs/budongi_mvp_temp/src/budongi/static/credentials.html", "outputs/budongi_mvp_temp/src/budongi/rental_readiness.py", "outputs/budongi_mvp_temp/tests/test_gms_budget.py", "outputs/budongi_mvp_temp/tests/test_rental_readiness.py", "outputs/budongi_mvp_temp/docs/specs/00_project_spec.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md", "outputs/budongi_mvp_temp/docs/tasks/rental-real-data.md", "outputs/budongi_mvp_temp/docs/tasks/rental-mvp.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/tasks/audit-personal-gms-20261021.md", "outputs/budongi_mvp_temp/docs/adr/ADR-023-personal-gms-ledger.md", "outputs/budongi_mvp_temp/docs/audit-personal-gms-validation-20261021.md", "outputs/budongi_mvp_temp/README.md", "outputs/budongi_mvp_temp/AGENTS.md", "AGENTS.md", "README.md", "docs/sdd/traceability.json"]
acs = ["GMS-BUDGET-001-AC-06", "RENT-001-AC-11"]

[[verification]]
command = "workspace TEMP/TMP: GMS budget44 + GMS12 + readiness8 + team27 unittest; node --check credentials.js; check_sdd.py --base origin/main; git diff --check; synthetic IAB A-B-A; real serving read-only audit"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/audit-personal-gms-validation-20261021.md"
acs = ["GMS-BUDGET-001-AC-06", "RENT-001-AC-11"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "failed"
evidence = "outputs/budongi_mvp_temp/docs/audit-personal-gms-validation-20261021.md"
acs = ["GMS-BUDGET-001-AC-06", "RENT-001-AC-11"]
```

Jira: [KAN-6](https://kwulreobeu.atlassian.net/browse/KAN-6).
승인: 2026-10-21 현재 사용자 요청. 문서 불일치·SDD 결과 형식·readiness 회귀를 검증하고 개인 할당 GMS 키별 정책/예약/자동 호출 내역을 구현한다.

- [ ] GMS-BUDGET-001-AC-06 키별 독립 정책·사용·보류·자동 정산, 재시작/동일 키 중복 등록/교체/이전 원장 보존, 비밀 비노출을 검증한다. 집중 검증 통과, 전체 검사 완료 대기.
- [ ] RENT-001-AC-11 기준 DB/날짜별 상태를 맞추고 SDD와 readiness 회귀·실제 읽기 전용 검증 증거를 남긴다. 문서/serving 재검증 통과, 원본 접근·전체 검사 대기.

전체 환경292개 중 수집 DB 임시 폴더 rename WinError5 1건으로 공식 검증은 failed다. canonical 원본 접근과 현재 실키 확인도 미완료이므로 Jira/Task는 진행 중을 유지한다. 기능별 검증을 제품/실키 전체 완료로 표시하지 않는다.

기존 사용자 변경은 유지한다. 새 수집·매칭·추천 차단 해제·키 자동 선택·push/merge는 포함하지 않는다.

# TASK-GMS-MODELS-001 — 난이도별 SOL/LUNA 코드 작업

```toml
kind = "task"
id = "TASK-GMS-MODELS-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/http_helpers.py", "outputs/budongi_mvp_temp/tests/test_http_helpers.py", "outputs/budongi_mvp_temp/src/budongi/rental_server.py", "outputs/budongi_mvp_temp/src/budongi/gms_models.py", "outputs/budongi_mvp_temp/src/budongi/gms_budget.py", "outputs/budongi_mvp_temp/src/budongi/gms_work.py", "outputs/budongi_mvp_temp/src/budongi/credential_server.py", "outputs/budongi_mvp_temp/src/budongi/static/credentials.html", "outputs/budongi_mvp_temp/src/budongi/static/credentials.js", "outputs/budongi_mvp_temp/tests/test_gms_budget.py", "outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md", "outputs/budongi_mvp_temp/docs/tasks/gms-model-routing.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/adr/ADR-012-gms-model-routing.md", "outputs/budongi_mvp_temp/docs/plans/continuation-parts-1to5.md", "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md", "outputs/budongi_mvp_temp/README.md", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", "docs/sdd/traceability.json"]
acs = ["GMS-BUDGET-001-AC-04", "GMS-BUDGET-001-AC-05"]

[[verification]]
command = "GMS budget tests 34 passed; selected runtime policy reserve_only/5000 verified after server restart; historical ledger retained"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/continuation-validation-20261014.md"
acs = ["GMS-BUDGET-001-AC-05"]
```

## 목적·근거

사용자의 난이도별 6.1 SOL/6.0 LUNA 요청을 기존 GMS budgeted runner에 구현한다. 공식 GMS 가이드에서 실제 ID와 요율을 확인했다. 단순=기계적·좁은 초안, 복잡=구조·보안·여러 동작 변경. 최신 지시대로 5,000 보존만 적용하고 누적은 기록으로 유지한다.

## 완료 기준

- [ ] GMS-BUDGET-001-AC-04 두 모델의 사전 카운트·요율·예약·정산·공통 원장·웹/CLI·실제 호출 확인.

- [x] GMS-BUDGET-001-AC-05 현재 정책은 reserve_only·5,000 보존이며 누적은 기록만 유지.

## 검증

[후속 검증](../continuation-validation-20261014.md)에 합성 회귀와 실제 호출을 분리해서 기록한다.

현재 두 모델 실제 호출·카운트/정산·CLI와 API 합성 회귀는 확인했다. 최신 설정 UI의 브라우저 검증은 자동 승인 서비스 한도 때문에 미완료이므로 AC-04/Task를 완료로 바꾸지 않는다.

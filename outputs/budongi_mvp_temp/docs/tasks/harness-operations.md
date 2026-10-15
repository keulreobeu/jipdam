# TASK-HARNESS-OPS-001

```toml
kind = "task"
id = "TASK-HARNESS-OPS-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/21_harness_operations_spec.md", "outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/jipdam_harness/", "outputs/budongi_mvp_temp/src/budongi/gms_budget.py", "outputs/budongi_mvp_temp/src/budongi/static/credentials.html", "outputs/budongi_mvp_temp/src/budongi/static/credentials.js", "outputs/budongi_mvp_temp/tests/test_gms_budget.py", "outputs/budongi_mvp_temp/tests/test_harness_operations.py", "outputs/budongi_mvp_temp/tests/test_managed_harness.py", "outputs/budongi_mvp_temp/tests/test_codex_gms_probe.py", "outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md", "outputs/budongi_mvp_temp/docs/specs/21_harness_operations_spec.md", "outputs/budongi_mvp_temp/docs/tasks/harness-operations.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/harness/", "outputs/budongi_mvp_temp/docs/adr/ADR-022-harness-operations.md", "docs/sdd/traceability.json", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", "README.md"]
acs = ["HARNESS-OPS-001-AC-01", "HARNESS-OPS-001-AC-02", "HARNESS-OPS-001-AC-03"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/verify_environment.py --gstack"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/harness/OPERATIONS_UPDATE_20261015.md#final-verification"
acs = ["HARNESS-OPS-001-AC-01", "HARNESS-OPS-001-AC-02", "HARNESS-OPS-001-AC-03"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/harness/OPERATIONS_UPDATE_20261015.md#final-verification"
acs = ["HARNESS-OPS-001-AC-03"]

```

- [x] HARNESS-OPS-001-AC-01 GMS 보존 정책·CLI 호환성 (당시 보존1,000은 후속 지시로 0으로 변경)
- [x] HARNESS-OPS-001-AC-02 안전한 자동 커밋
- [x] HARNESS-OPS-001-AC-03 운영·실제 Git 기록·회귀

사용자 추가 지시는 기존 CLI-HARNESS 구현 Goal의 후속 범위다. 기존 5,000/1,000은 이력이고 현재 고정 보존액은0이다.

## 후속 검증 보완

검증 subprocess의 PYTHONPATH를 작업 worktree의 제품/src와 src로 고정했다.
App 원본 checkout의 editable 설치/환경 경로로 잘못된 코드를 시험하지 않도록 실제 수정 소스 import 검사로 검증했다.

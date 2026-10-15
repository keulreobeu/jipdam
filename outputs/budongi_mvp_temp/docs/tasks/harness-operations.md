# TASK-HARNESS-OPS-001

```toml
kind = "task"
id = "TASK-HARNESS-OPS-001"
status = "in_progress"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/21_harness_operations_spec.md", "outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/jipdam_harness/", "outputs/budongi_mvp_temp/src/budongi/gms_budget.py", "outputs/budongi_mvp_temp/src/budongi/static/credentials.html", "outputs/budongi_mvp_temp/src/budongi/static/credentials.js", "outputs/budongi_mvp_temp/tests/test_gms_budget.py", "outputs/budongi_mvp_temp/tests/test_harness_operations.py", "outputs/budongi_mvp_temp/tests/test_codex_gms_probe.py", "outputs/budongi_mvp_temp/docs/specs/18_gms_budget_spec.md", "outputs/budongi_mvp_temp/docs/specs/21_harness_operations_spec.md", "outputs/budongi_mvp_temp/docs/tasks/harness-operations.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/harness/", "outputs/budongi_mvp_temp/docs/adr/ADR-022-harness-operations.md", "docs/sdd/traceability.json", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", "README.md"]
acs = ["HARNESS-OPS-001-AC-01", "HARNESS-OPS-001-AC-02", "HARNESS-OPS-001-AC-03"]
```

- [ ] HARNESS-OPS-001-AC-01 보존1000·GMS CLI 호환성
- [ ] HARNESS-OPS-001-AC-02 안전한 자동 커밋
- [ ] HARNESS-OPS-001-AC-03 운영·실제 Git 기록·회귀

사용자 추가 지시는 기존 CLI-HARNESS 구현 Goal의 후속 범위다. 기존 5,000은 이력이고 현재는1,000이다.

# TASK-LEAN-METRICS-001 / KAN-42

```toml
kind = "task"
id = "TASK-LEAN-METRICS-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/32_lean_foundations_spec.md", "outputs/budongi_mvp_temp/docs/specs/28_observability_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/jipdam_harness/observability.py", "outputs/budongi_mvp_temp/src/jipdam_harness/metrics_cli.py", "outputs/budongi_mvp_temp/src/jipdam_harness/orchestrator.py", "outputs/budongi_mvp_temp/src/jipdam_harness/managed.py", "outputs/budongi_mvp_temp/tests/test_lean_metrics.py", "outputs/budongi_mvp_temp/tests/test_observability.py", "outputs/budongi_mvp_temp/docs/specs/32_lean_foundations_spec.md", "outputs/budongi_mvp_temp/docs/tasks/lean-metrics.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/plans/lean-foundations-20261103.md", "outputs/budongi_mvp_temp/docs/harness/OBSERVABILITY.md", "outputs/budongi_mvp_temp/docs/harness/LEAN_VALIDATION_20261103.md", "docs/sdd/traceability.json"]
acs = ["LEAN-CORE-001-AC-07", "LEAN-CORE-001-AC-08", "LEAN-CORE-001-AC-09", "LEAN-CORE-001-AC-10", "LEAN-CORE-001-AC-11", "LEAN-CORE-001-AC-12"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/harness/LEAN_VALIDATION_20261103.md"
acs = ["LEAN-CORE-001-AC-07", "LEAN-CORE-001-AC-08", "LEAN-CORE-001-AC-09", "LEAN-CORE-001-AC-10", "LEAN-CORE-001-AC-11", "LEAN-CORE-001-AC-12"]
```

- [x] LEAN-CORE-001-AC-07 단위별 counts/provenance.
- [x] LEAN-CORE-001-AC-08 usage 산술·cache/reasoning.
- [x] LEAN-CORE-001-AC-09 결측/과거 metadata unknown.
- [x] LEAN-CORE-001-AC-10 실패 bucket·수동 관측·품질 gate 분리.
- [x] LEAN-CORE-001-AC-11 실패/수리 누적·성공0null.
- [x] LEAN-CORE-001-AC-12 기존 원장/실패4건/1085783토큰 불변.

기존 OBS-001은 대부분 M-02/03/05/06을 지원한다. 재작성하지 않고 차이만 구현한다.
현재 invocation.finished는 error bucket을 보존하지 않고 explicit purpose/counts가 없다.
이를 bounded optional metadata/report 필드로 추가하며 원래 rows/평가를 소급 갱신하지 않는다.
구현 후 로컬 계측10개와 기존 OBS32개를 통과했다. 실제 임시 managed 작업의
검증 실패→repair와 이후 수동 재개의 unknown 분류를 확인했다. 시도 한도를 우회하지 않고
합성 작업에3회를 명시해 검증했다. 최신 전체 회귀·고정 SHA 독립 검토/게시 전이다.

최신 전체 검증: 제품411/팀35/합성CLI passed. 독립 검토·최종 게시 전이라 status는 in_progress다.

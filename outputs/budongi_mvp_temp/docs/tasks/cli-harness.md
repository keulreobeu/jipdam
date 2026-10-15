# TASK-CLI-HARNESS-001

```toml
kind = "task"
id = "TASK-CLI-HARNESS-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/20_cli_harness_spec.md"]
scope = ["harness/", "scripts/install_codex_cli.ps1", "outputs/budongi_mvp_temp/src/jipdam_harness/", "outputs/budongi_mvp_temp/tests/test_managed_harness.py", "outputs/budongi_mvp_temp/tests/test_managed_providers.py", "outputs/budongi_mvp_temp/tests/test_managed_planning.py", "outputs/budongi_mvp_temp/docs/specs/20_cli_harness_spec.md", "outputs/budongi_mvp_temp/docs/tasks/cli-harness.md", "outputs/budongi_mvp_temp/docs/tasks/molit-statistics-history.md", "outputs/budongi_mvp_temp/docs/plans/cli-harness.md", "outputs/budongi_mvp_temp/docs/adr/ADR-021-cli-harness.md", "outputs/budongi_mvp_temp/docs/harness/", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json", "AGENTS.md", "outputs/budongi_mvp_temp/AGENTS.md", "README.md"]
acs = ["CLI-HARNESS-001-AC-01", "CLI-HARNESS-001-AC-02", "CLI-HARNESS-001-AC-03", "CLI-HARNESS-001-AC-04"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/verify_environment.py --gstack"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/harness/CLI_IMPLEMENTATION_REPORT.md#final-verification"
acs = ["CLI-HARNESS-001-AC-01", "CLI-HARNESS-001-AC-02", "CLI-HARNESS-001-AC-03", "CLI-HARNESS-001-AC-04"]

```

사용자 요청: 첨부 계획 구현, CLI 설치, Goal 등록. HARNESS-001 기존 변경과 제품 데이터 경계를 보존한다.

- [x] CLI-HARNESS-001-AC-01 영속 관리
- [x] CLI-HARNESS-001-AC-02 격리·복구
- [x] CLI-HARNESS-001-AC-03 Provider·예산
- [x] CLI-HARNESS-001-AC-04 운영·보안·회귀

## 구현·GMS 활용 기록

LUNA Planner 코드·수용 테스트·운영 복구 문서·기능 검토 초안을 검토해 반영했다.
SOL 결과 불확실 예약은 보존했으며 재시도하지 않았다. 최종 잔액 29,092와 보류183/보존5,000 확인.
자세한 호출/한계/독립 리뷰는 [구현 검증 기록](../harness/CLI_IMPLEMENTATION_REPORT.md).
기존 수집 Task의 미등록 AC를 실제 MOLIT Spec AC 메타데이터로만 정리해 전체 SDD 검사를 복구했다.
수집 범위·진행·완료 상태는 변경하지 않았다.

## 팀 공유용 CLI 안내 후속

2026-10-15 팀원 공유용 [하네스·CLI 요약](../harness/TEAM_GUIDE.md)을 추가하고 저장소 README와 하네스 안내에서 연결했다.
Codex CLI 자동 provider와 Claude Code/Antigravity의 수동 인계·미검증 경계를 구분하고, 향후 provider 확장에 필요한 검증 항목을 정리했다.

[[verification]]
command = "python -X utf8 scripts/check_sdd.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/harness/TEAM_GUIDE.md#빠른-진실-확인"
acs = ["CLI-HARNESS-001-AC-04"]

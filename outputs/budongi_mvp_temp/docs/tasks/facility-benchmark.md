# TASK-BENCH-FACILITY-001 — 실제 시설 검증기와 Objective 비교

```toml
kind = "task"
id = "TASK-BENCH-FACILITY-001"
status = "in_progress"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/29_facility_package_validation_spec.md", "outputs/budongi_mvp_temp/docs/specs/30_context_benchmark_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/team_package.py", "outputs/budongi_mvp_temp/tests/test_team_package.py", "outputs/budongi_mvp_temp/tests/test_team_package_acceptance.py", "outputs/budongi_mvp_temp/src/jipdam_harness/execution.py", "outputs/budongi_mvp_temp/src/jipdam_harness/managed.py", "outputs/budongi_mvp_temp/tests/test_managed_providers.py", "outputs/budongi_mvp_temp/tests/test_managed_harness.py", "outputs/budongi_mvp_temp/scripts/benchmark_facility.py", "outputs/budongi_mvp_temp/tests/test_facility_benchmark.py", "outputs/budongi_mvp_temp/docs/specs/29_facility_package_validation_spec.md", "outputs/budongi_mvp_temp/docs/specs/30_context_benchmark_spec.md", "outputs/budongi_mvp_temp/docs/adr/ADR-027-controlled-facility-benchmark.md", "outputs/budongi_mvp_temp/docs/plans/facility-benchmark.md", "outputs/budongi_mvp_temp/docs/tasks/facility-benchmark.md", "outputs/budongi_mvp_temp/docs/harness/FACILITY_BENCHMARK.md", "outputs/budongi_mvp_temp/docs/team-data-contract.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/docs/wiki/pages/"]
acs = ["FACILITY-PACKAGE-001-AC-01", "FACILITY-PACKAGE-001-AC-02", "FACILITY-PACKAGE-001-AC-03", "FACILITY-PACKAGE-001-AC-04", "FACILITY-PACKAGE-001-AC-05", "FACILITY-PACKAGE-001-AC-06", "BENCH-CONTEXT-001-AC-01", "BENCH-CONTEXT-001-AC-02", "BENCH-CONTEXT-001-AC-03", "BENCH-CONTEXT-001-AC-04"]
```

Jira [KAN-31](https://kwulreobeu.atlassian.net/browse/KAN-31), agent-codex, 진행 중. 실제 구현은
measured Codex CLI가 담당하며 부모는 명세/독립 평가/검토/적용/문서를 담당한다.

- [ ] FACILITY-PACKAGE-001-AC-01 manifest
- [ ] FACILITY-PACKAGE-001-AC-02 hash/bytes/rows
- [ ] FACILITY-PACKAGE-001-AC-03 facility/envelope
- [ ] FACILITY-PACKAGE-001-AC-04 counts
- [ ] FACILITY-PACKAGE-001-AC-05 structured errors
- [ ] FACILITY-PACKAGE-001-AC-06 deterministic/read-only
- [ ] BENCH-CONTEXT-001-AC-01 preflight/smoke/seal
- [ ] BENCH-CONTEXT-001-AC-02 objective-only option
- [ ] BENCH-CONTEXT-001-AC-03 fixed trials/independent approval
- [ ] BENCH-CONTEXT-001-AC-04 complete comparison/delivery

## 시작 증거

CLI0.164.0·ChatGPT 로그인·현재 모델gpt-6.1-terra/high·provider openai를 값 노출 없는
preflight로 확인했다. API 인증으로 전환하지 않는다. 기존 source HEAD f01faa와 다수 dirty
작업은 보존하며 main b29d2d4에서 이번 변경만 따로 구성한다. Git 쓰기는 전담 서브에이전트다.
아직 actual token 측정/절감 성과는 없다. 기획/문서 작성의 App 사용량은 자동 계측 범위 밖이다.

## 실행·검증

사전 비과금 검사: 기존 관측성32개, provider17개(기존15+objective2), managed14개(기존13+모드
호환1), benchmark 제어/음성대조8개 PASS. SDD features27/AC133/tasks56 PASS.
memories와 external_agent_memory_import는 false, API 키 환경변수 존재 없음 확인. GMS 로컬
draft 서버는 unavailable로 이번 Codex 비교에는 호출하지 않았고 예산 정책은 유지했다.
gstack Bash preamble은 Windows OS 객체 생성 권한으로 degraded이며 native 읽기 전용 계획
검토를 사용했다. 고정 명세/평가를 구현자의 수정 scope 밖에 두되 숨겨진 평가라고 주장하지 않는다.

실제 실행과 독립 검증 뒤 원시 숫자/해시·실패를 요약한다. 합성 package의 실제 모델 개발
비용과 실제 데이터 수집/품질을 혼동하지 않는다. spec·eval은 첫 모델 구현 전에 봉인한다.

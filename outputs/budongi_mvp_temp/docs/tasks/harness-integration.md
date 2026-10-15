# TASK-HARNESS-001 — Mock 기반 최소 공통 하네스

```toml
kind = "task"
id = "TASK-HARNESS-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/19_harness_spec.md"]
scope = ["scripts/register_gstack.py", "tests/test_harness_discovery.py", "outputs/budongi_mvp_temp/src/jipdam_harness/", "outputs/budongi_mvp_temp/tests/test_harness.py", "outputs/budongi_mvp_temp/tests/test_harness_gateway.py", "scripts/agent_harness.py", "outputs/budongi_mvp_temp/docs/specs/19_harness_spec.md", "outputs/budongi_mvp_temp/docs/adr/ADR-020-portable-harness.md", "outputs/budongi_mvp_temp/docs/plans/harness-integration.md", "outputs/budongi_mvp_temp/docs/tasks/harness-integration.md", "outputs/budongi_mvp_temp/docs/harness/", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json", ".codex/agents/", ".codex/config.toml", ".agents/skills/jipdam-harness/"]
acs = ["HARNESS-001-AC-01", "HARNESS-001-AC-02", "HARNESS-001-AC-03", "HARNESS-001-AC-04", "HARNESS-001-AC-05"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/verify_environment.py --gstack"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/harness/validation.md#final-verification"
acs = ["HARNESS-001-AC-01", "HARNESS-001-AC-02", "HARNESS-001-AC-03", "HARNESS-001-AC-04", "HARNESS-001-AC-05"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/harness/validation.md#검증"
acs = ["HARNESS-001-AC-05"]
```

사용자의 2026-10-14 현재 요청·제공 구현 지시문을 근거로 최소 공통 하네스를 구현한다.
초기 요청의 GMS 실제 호출 금지로 quote/count/키 조회 없이 구현했다. 이후 사용자가
"이거 작업할때도 GMS 사용해도 될듯"으로 현재 작업의 기존 예산 runner 사용을 추가 허용했다.
새 Mock gateway의 live 차단과 실할당/API 미검증 게이트는 유지한다. 기존 runner의 문서 초안
시도는 입력 count 1회 20크레딧 후 전체500크레딧 한도에 차단됐으며 생성0회다. 추가 재시도·한도 변경은 하지 않았다.
실제 제품 설명/실GMS/Claude·Antigravity native hook은 이번 완료 조건에 포함하지 않는다.

## 완료 기준

- [x] HARNESS-001-AC-01 저장·중단·재개·중복·cursor·AC 게이트
- [x] HARNESS-001-AC-02 범위/해시/lease/키 fixture 검사
- [x] HARNESS-001-AC-03 공통 호스트 인계와 native 상태 구분
- [x] HARNESS-001-AC-04 Mock 예산·장애·캐시·호출 전 차단
- [x] HARNESS-001-AC-05 Phase 0·회귀·SDD·실행 기록

## 실행 기록

Phase 0: source_assessment 실제 native subagent 실행, 읽기 전용 ZIP/기존 GMS 분석 완료.
Master는 설계/구현, harness_review는 독립 리뷰/재현/재검증, harness_evaluator는 독립 테스트를 수행했다.
에이전트 실제 토큰은 도구 미제공으로 unknown. 새 gateway live0회, 기존 runner 생성0회,
유료 count1회20크레딧(계수 요청의 청구 토큰 미제공). Mock 예제 usage는 합성23토큰이다.
자세한 파일·해시·실행 결과는 [검증 기록](../harness/validation.md)과 [출처](../harness/origins.md)에 보존한다.

## 결과

Bounded offline HARNESS-001 AC01~05 검증 완료. 코어16·제품225·팀27·CLI6·SDD·고정gstack58 통과. 실제GMS gateway/타호스트 native·실제 할당/제품 품질은 완료 범위 밖이며 검증 문서의 not_run/partial을 유지한다. 사용자 추가 GMS 허용은 기존500크레딧 한도 증액 승인이 아니다.

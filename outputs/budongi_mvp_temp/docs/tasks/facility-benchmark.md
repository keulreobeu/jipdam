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

- [x] FACILITY-PACKAGE-001-AC-01 manifest
- [x] FACILITY-PACKAGE-001-AC-02 hash/bytes/rows
- [x] FACILITY-PACKAGE-001-AC-03 facility/envelope
- [x] FACILITY-PACKAGE-001-AC-04 counts
- [x] FACILITY-PACKAGE-001-AC-05 structured errors
- [x] FACILITY-PACKAGE-001-AC-06 deterministic/read-only
- [x] BENCH-CONTEXT-001-AC-01 preflight/smoke/seal
- [x] BENCH-CONTEXT-001-AC-02 objective-only option
- [x] BENCH-CONTEXT-001-AC-03 fixed trials/independent approval
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

## 실제 결과와 인계 — 2026-10-30

[영구 보고서·다른 환경 재개 절차](../harness/FACILITY_BENCHMARK.md)에 조건/수치/Run ID/
원본 해시/실패 비용/절차 이탈을 기록했다. 공통 C_SHA=d6cc4badb2c52dea0a6f72f70fb5c9085c77491e,
manifest SHA=fa08475c47e9996bdb3172b826fd6b72386dccccb12e71935771dddb67ba3ccc.
A1/B1/B2/A2는293,537/316,935/236,538/238,773토큰(합계1,085,783), 모두 complete/attempt1/
retry0이다. 별도 smoke23,404토큰은 제외했다. 고정19개는 통과했지만 추가 독립 검토 결함으로
4회 모두 review/approval=false, verified success0/4, 성공당 토큰/절감률null이다. 측정 worker/
evaluator는 수정하지 않았고 rejected 상태와 비용을 보존했다. 원본 driver의 성공 전제 진행
gate는 runtime adapter로 우회해 부정 outcome을 기록한 뒤 순서대로 진행했으며 입력 hash는
봉인과 같았다. 최종 driver에는 evidence/revision을 검사하는 reject 명령을 정식 추가했다.

제품은 B2 기반 **실측 밖 보완**이다. 긴 CSV 숫자의 int 변환 crash, schema.json=null,
refresh_token URL 누락, 깊은 JSON RecursionError를 각각 실패 재현 후 수정했다. 최종
public9+frozen19=28 PASS, benchmark control10 PASS. 기존 obs32/provider17/managed14는
준비 단계 PASS이며 최종 publisher 환경 검사로 다시 확인한다. native 독립 최종 재검토는
두 JSON parser 경로의 수정/재현을 확인하고 추가 결함 없음을 보고했다. 첫 리뷰 agent의
재검토는 사용량 한도로 실패했으며 다른 native reviewer가 완료했다. 외부 CLI 리뷰는 안 했다.

사용자의 최신 마무리/다른 환경 인계 요청에 따라 추가 actual 모델 실행은 중단한다.
새 실험은 강화한 평가를 먼저 봉인하고 새 study/task/state-dir로 시작한다. 과거 원장은
자동 전송하지 않으며 인증/키/DB/raw/runtime을 Git에 넣지 않는다. once는 opt-in으로 유지한다.

## 위키 영수증

maintenance/catalog/ACTIVE search와 지정 공간 CQL/문서 ID 중복 검색을 수행했다. 기존 관측성
가이드와 다른 재사용 주제로 CREATE: TASK-BENCH-FACILITY-001-VERIFIED-1 /
WIKI-140772C1B2DAC3D0 revision1. [Confluence](https://kwulreobeu.atlassian.net/wiki/spaces/~7120201d82685826914674999dcbf004921921/pages/2555905)
read-back v1, HTML SHA=038c3ecdaefa8db5f77c2365ff9c548e061f7ec5def8614af775cd9588bab52d,
보고서 source SHA=fd4922075d87fa431c2ca9711e3d0ef9ac69ea4bdc9062349d138b988f2e0584.
문서/Jira outbox receipt DONE, decision blocking=false/DONE. Jira 댓글10149/10150.
기존 pipeline STALE/outbox는 범위 밖으로 보존했다. 생성된 wiki export는 로컬/Confluence에
보존하며 이번 Git exact18 scope에는 넣지 않는다. 다른 환경은 위 원격 stable ID를 재사용한다.

## 최종 저장 상태

Git preparation은 codex/facility-benchmark-kan31의 d6cc4bad로 원격 확인됐다. 제품 보완/
보고서의 최종 snapshot·publisher 검증·CI·merge commit 및 원격 read-back은 진행 중이다.
Git 담당자는 merge commit을 사용해 C_SHA가 main 조상으로 남는지 확인한다. 기존 dirty
source f01faa/다른 작업/index와 측정 worktree는 보존한다. 완료 영수증이 없으면 다음 담당자는
KAN-31을 진행 중으로 유지하고 최종 Git 저장부터 확인한다.

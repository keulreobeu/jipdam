# TASK-RENT-DOC-001 — 전월세 추천 SDD 문서 전환

```toml
kind = "task"
id = "TASK-RENT-DOC-001"
status = "verified"
owner = "Codex"
specs = ["docs/specs/sdd_workflow_spec.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["AGENTS.md", "README.md", ".agents/skills/jipdam-workflow/SKILL.md", "docs/sdd.md", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/AGENTS.md", "outputs/budongi_mvp_temp/README.md", "outputs/budongi_mvp_temp/docs/"]
acs = ["SDD-001-AC-01", "SDD-001-AC-02", "SDD-001-AC-03", "SDD-001-AC-04", "RENT-001-AC-11"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/rental-spec-transition.md#doc-validation"
acs = ["SDD-001-AC-01", "SDD-001-AC-02", "SDD-001-AC-03", "SDD-001-AC-04"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/rental-spec-transition.md#doc-validation"
acs = ["SDD-001-AC-04", "RENT-001-AC-11"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/rental-spec-transition.md#doc-validation"
acs = ["SDD-001-AC-03", "SDD-001-AC-04"]

[[verification]]
command = "manual: 승인 Plan 대비 문서 계약·CURRENT/EVAL 보존·Task 의존·링크/앵커·제품 not_run/수집 blocked 검토; git diff --check"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/rental-spec-transition.md#doc-validation"
acs = ["SDD-001-AC-02", "SDD-001-AC-04", "RENT-001-AC-11"]
```

## 목표·확정 근거

변경 유형: 제품 계약·중요 구조·문서 변경. 승인된 [PLAN-RENT-001](../plans/rental-recommendation-mvp.md#확정-근거)의 사용자 `PLEASE IMPLEMENT THIS PLAN` 요청에 따라 [RENT-001](../specs/10_rental_recommendation_spec.md)·ADR·Plan·Task·원장을 작성하고 기존 문서와 작업 규칙의 TARGET를 동기화한다. 재승인·GitHub issue·제품 코드 구현은 이번 범위가 아니다.

기존 사용자 환경 변경(`TASK-ENV-001`, 원장 등록, 환경 검증 기록과 current 링크)과 EVAL-001 baseline/Task/AC 이력은 보존한다. CURRENT의 역사 DB·Tool·CLI를 바꾸지 않는다. 실제 수집·단지 매칭 보류를 유지한다.

## 완료 기준

- [x] SDD-001-AC-01 신규 Spec/Task ID·TOML 상태·승인 근거가 유효하다.
- [x] SDD-001-AC-02 요구·AC·수동 검증 계획·후속 Task·증거 문서 참조가 유효하다.
- [x] SDD-001-AC-03 변경 계약은 같은 변경의 영구 문서 Task scope에 연결된다.
- [x] SDD-001-AC-04 문서 완료는 실제 검사·수동 검토 증거로 기록하며 미실행 제품 AC와 분리한다.
- [x] RENT-001-AC-11 Spec·Plan·ADR·원장·AGENTS·README·기존 TARGET와 적용 범위가 일치한다.

SDD 운영 자체의 도입 완료·외부 CI·main 보호 설정을 이번에 다시 검증했다고 주장하지 않는다. 위 SDD AC는 이번 문서 변경에 대한 구조·참조·scope·완료 기록 검증이다.

## doc-validation

2026-10-06, Python 3.12.10에서 실행했다. `check_sdd.py`와 `--base origin/main`은 3개 feature·23개 AC·9개 Task·28개 변경 경로 검사에서 passed였다. `verify_environment.py`는 SDD 검사, 제품 28개·루트 18개 테스트, 모델 없는 합성 CLI 검사를 통과했다. `git diff --check`는 exit 0이었다. 이 검사들은 기존 기반과 문서 적용의 증거이며 신규 전월세 제품 테스트가 아니다.

수동 검토에서는 승인 Plan의 유지/추가/후순위 목록, CURRENT·EVAL-001 보존, 같은 계약의 예산·최신성, 필수/선호·미확인, 설명 fallback, 문서/제품 완료 경계와 발견성을 대조했다. 최종 변경 Markdown의 로컬 링크·앵커 157개에 누락이 없었다. 내부 독립 검토의 P2 1건(REC 완료 조건에 후속 웹 검증 포함)은 수정했고 재확인에서 추가 이슈가 없었다. AC-08은 WEB Task가 소유하며 REC→WEB의 순차 완료가 가능하다.

Plan의 마지막 `GSTACK REVIEW REPORT`와 `NO UNRESOLVED DECISIONS`를 읽어 확인한 후 프로젝트의 기존 Git for Windows/Bun을 사용해 `gstack-review-log`를 실행했다. 2026-10-06T05:57:56Z의 `plan-eng-review` 레코드는 `.local_runtime/gstack/projects/keulreobeu-jipdam/main-reviews.jsonl`에 저장됐고 `gstack-review-read`에서 확인했다. `issues_open`은 수정한 발견 1건의 보존 표기이며 `unresolved=0`, `critical_gaps=0`, `findings_fixed=1`이다. 외부 CLI는 skipped, 내부 검토 provenance를 기록했다. 이 로그는 로컬 검토 기록이며 원격 동기화·외부 리뷰·전체 릴리스 완료 증거가 아니다.

제품 AC-01~10은 [Plan의 미실행 검증 계획](../plans/rental-recommendation-mvp.md#product-verification-pending)으로 남기고 여기서 체크하지 않는다. 기존 환경 수정 Task와 EVAL 원장·평가 기록을 덮어쓰지 않았다.

## 후속 작업·완료 한계

문서 완료 후 첫 제품 작업은 [TASK-RENT-DATA-001](rental-data-contract.md)의 원천 기술문서 대조·합성 전월세/위치/시설 적재 계약이다. 실제 다운로드·매칭은 [TASK-RENT-REAL-001](rental-real-data.md)의 사용자 보류 해제 전까지 blocked다. 새 recommend/웹/LLM 설명은 아직 구현되지 않았다.

# TASK-CRED-DOC-001 — 자격증명 보관함 SDD 반영

```toml
kind = "task"
id = "TASK-CRED-DOC-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["docs/sdd.md", "docs/sdd/traceability.json", ".agents/skills/jipdam-workflow/SKILL.md", "outputs/budongi_mvp_temp/AGENTS.md", "outputs/budongi_mvp_temp/README.md", "outputs/budongi_mvp_temp/docs/specs/00_project_spec.md", "outputs/budongi_mvp_temp/docs/specs/09_runtime_spec.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md", "outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md", "outputs/budongi_mvp_temp/docs/adr/ADR-004-local-api-credential-vault.md", "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md", "outputs/budongi_mvp_temp/docs/tasks/api-credential-vault.md", "outputs/budongi_mvp_temp/docs/tasks/credential-vault-sdd.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/docs/tasks/rental-data-contract.md", "outputs/budongi_mvp_temp/docs/tasks/rental-web-demo.md"]
acs = ["CRED-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-vault-sdd.md#doc-validation"
acs = ["CRED-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-vault-sdd.md#doc-validation"
acs = ["CRED-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-vault-sdd.md#doc-validation"
acs = ["CRED-001-AC-06"]

[[verification]]
command = "git diff --check"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-vault-sdd.md#doc-validation"
acs = ["CRED-001-AC-06"]
```

## 목표·확정 근거

사용자 요청에 따라 신규 전월세 API 키의 암호화 저장, 공급자별 복수 키·키별 별칭, 폴더 분류와 폴더 삭제 시 자식 키 삭제를 CRED-001·ADR-004·전환 Plan·Task·원장에 반영한다. 사용자는 암호화 키를 Windows 계정에 묶인 OS 자격 증명 저장소(Windows Credential Manager)에 보관하는 방식을 선택했다. 기존 역사 수집의 환경변수 계약, 제품 미구현 상태, 실수집 보류를 보존한다.

## 완료 기준

- [x] CRED-001-AC-06 SDD 반영: Spec·ADR·Plan·Task·원장·runtime·개발 규칙·README가 서로 일치하며, Windows OS 자격 증명 저장소 선택과 fail-closed 경계, 제품 Task의 `draft`/미실행 AC `not_run`, 실제 API 호출·결제 제외를 기록한다.

## doc-validation

`python -X utf8 scripts/check_sdd.py`, `python -X utf8 scripts/verify_environment.py`, `python -X utf8 scripts/check_sdd.py --base origin/main`, `git diff --check`가 모두 통과했다. 환경 검증은 제품 34개 테스트, SDD 18개 테스트와 합성 CLI smoke도 통과했다. 이 Task 완료는 문서 적용 검증만 뜻하며 보관함 구현·암호화 보안 평가·공급자 API 호출 완료를 뜻하지 않는다.

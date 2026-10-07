# TASK-CRED-001 — 암호화 API 키 보관함

```toml
kind = "task"
id = "TASK-CRED-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/", "outputs/budongi_mvp_temp/tests/", "outputs/budongi_mvp_temp/docs/specs/00_project_spec.md", "outputs/budongi_mvp_temp/docs/specs/09_runtime_spec.md", "outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md", "outputs/budongi_mvp_temp/docs/plans/rental-recommendation-mvp.md", "outputs/budongi_mvp_temp/docs/tasks/api-credential-vault.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/AGENTS.md", "outputs/budongi_mvp_temp/README.md", "outputs/budongi_mvp_temp/pyproject.toml", "docs/sdd.md", "docs/sdd/traceability.json"]
acs = ["CRED-001-AC-01", "CRED-001-AC-02", "CRED-001-AC-03", "CRED-001-AC-04", "CRED-001-AC-05"]

[[verification]]
command = "python -m unittest discover -s tests -p test_credentials.py -v"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/api-credential-vault.md#validation"
acs = ["CRED-001-AC-01", "CRED-001-AC-02", "CRED-001-AC-04"]

[[verification]]
command = "python -m unittest discover -s tests -p test_credential_server.py -v"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/api-credential-vault.md#validation"
acs = ["CRED-001-AC-03", "CRED-001-AC-04", "CRED-001-AC-05"]

[[verification]]
command = "node --check src/budongi/static/credentials.js"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/api-credential-vault.md#validation"
acs = ["CRED-001-AC-03"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/api-credential-vault.md#validation"
acs = ["CRED-001-AC-01", "CRED-001-AC-03", "CRED-001-AC-04", "CRED-001-AC-05"]

[[verification]]
command = "manual: local browser flow with synthetic in-memory key store: create folder, save synthetic key, verify masked listing/input clearing, confirm folder cascade delete, inspect console"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/api-credential-vault.md#validation"
acs = ["CRED-001-AC-01", "CRED-001-AC-03", "CRED-001-AC-04", "CRED-001-AC-05"]

[[verification]]
command = "temporary venv: python -X utf8 scripts/bootstrap.py --app-only; current Windows user Credential Manager synthetic-key write/read/delete round-trip passed"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/api-credential-vault.md#validation"
acs = ["CRED-001-AC-02"]
```

## 목표·근거

로컬 전월세 앱에서 공급자별 API 키를 Windows 계정 범위 OS 자격 증명 저장소로 보호하는 암호화 보관함을 구현한다. 사용자가 여러 폴더와 키별 별칭을 관리하고, 폴더 삭제 시 포함한 키 전체가 트랜잭션으로 삭제되도록 한다. 사용자 결정과 암호화 계약은 [CRED-001](../specs/11_api_credential_vault_spec.md), 선택 이유는 [ADR-004](../adr/ADR-004-local-api-credential-vault.md), 제품 흐름은 [PLAN-RENT-001](../plans/rental-recommendation-mvp.md)을 따른다.

이번 Task는 로컬 보관함 UI/API·암호화 저장 기반만 구현한다. 실제 국토부·Kakao·서울시 API 호출, 임대차 수집·단지/시설 매칭, 유료 쿼터 활성화는 포함하지 않는다. 기존 역사 importer의 환경변수는 보존한다.

## 의존·제외 범위

선행 조건: [TASK-RENT-REC-001](rental-recommendation-cli.md)의 추천·CLI 계약 확인. 이 Task에서 Python loopback settings server의 공통 기반을 제공하고, [TASK-RENT-WEB-001](rental-web-demo.md)이 이를 통합한다. 저장소가 없을 때 fail-closed, 보안 테스트 가능, secret 입력·오류·삭제 시나리오 정의. 실제 공급자 호출은 [TASK-RENT-REAL-001](rental-real-data.md)의 별도 보류 해제 뒤에만 다룬다.

외부 배포·원격 secret manager·키 공유·자동 쿼터 증설·유료 결제·현재 API 호출은 제외한다. 담당자는 착수 시 구현 환경에서 Windows Credential Manager 사용 가능 여부를 확인한다.

## 완료 기준

- [x] CRED-001-AC-01 여러 키·별칭·영속성
- [x] CRED-001-AC-02 암호문 저장·복호화 실패; 합성 crypto/fail-closed 검증 및 현재 Windows 사용자 Credential Manager 합성 키 round-trip 통과
- [x] CRED-001-AC-03 비밀값 비노출
- [x] CRED-001-AC-04 폴더 삭제 cascade
- [x] CRED-001-AC-05 저장 동작의 무통신·사용자 선택

## validation

아래는 최초 구현 검증 기록이다. 후속 검토에서 발견한 문제와 현재 검증 결과는 [TASK-CRED-QA-001](credential-vault-qa.md#validation)을 따른다. 최초 스크린샷 실패는 캡처 명령의 Windows 경로 해석 문제였으며, 후속 QA에서는 절대 `/` 경로로 데스크톱·모바일 캡처를 완료했다. 최초 자동 실행 세션에서는 native OS round-trip을 실행하지 못했으며, 2026-10-07 현재 Windows 사용자 세션 검증 결과를 아래에 추가했다.

보관함·loopback 서버·설정 UI를 구현했다. 전체 제품 테스트 54개, SDD 테스트 18개, JavaScript 문법 검사와 로컬 브라우저 흐름이 통과했다. 전체 테스트 중 합성 키 기반 vault 13개(통과 12·최초 Windows native integration 1개는 managed 세션에 로그온 Credential Manager 세션이 없어 skip), HTTP/UI API 7개가 포함된다. 브라우저에서는 임시 DB와 메모리 전용 합성 키 저장소로 폴더 생성, 합성 키 저장, 키 입력 초기화·마스킹, 확인 대화상자를 거친 폴더 cascade 삭제를 수행했고 콘솔 오류가 없었다. 암호문 DB·재시작 복호화·오염 탐지·키 저장소 오류의 fail-closed·별칭 redaction·폴더 cascade/rollback·loopback/Host/Origin/CSRF·응답 비노출도 테스트했다. 스크린샷 캡처는 gstack 브라우저의 locator screenshot 5초 제한으로 완료되지 않았다. 최초 자동 실행 세션에서는 native API가 `CredWriteW` 오류 1312를 반환했고 평문 fallback은 하지 않았다. 실제 API 키는 테스트 fixture·로그·Git에 넣지 않았다.

2026-10-07 후속 검증: 임시 Python 3.12 가상환경에 `python -m pip install -e outputs/budongi_mvp_temp`로 앱과 의존성을 설치한 뒤 `python -X utf8 scripts/bootstrap.py --app-only`를 실행했다. 제품 테스트 82개, SDD·팀 테스트 18개와 합성 CLI smoke가 통과했다. `test_native_credential_manager_round_trip_uses_synthetic_key`가 현재 Windows 사용자 Credential Manager에 UUID 대상·합성 키를 저장하고 읽고 삭제하는 왕복을 통과했다. CRED-001-AC-02 검증은 완료했다. 외부 API 호출·실데이터 수집·실제 자격증명 사용은 하지 않았다.

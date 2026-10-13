# TASK-CRED-ALIAS-001 — 별칭·폴더로 키 관리 통일

```toml
kind = "task"
id = "TASK-CRED-ALIAS-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/credential_vault.py", "outputs/budongi_mvp_temp/src/budongi/credential_server.py", "outputs/budongi_mvp_temp/src/budongi/static/credentials.html", "outputs/budongi_mvp_temp/src/budongi/static/credentials.js", "outputs/budongi_mvp_temp/src/budongi/collection.py", "outputs/budongi_mvp_temp/tests/test_credentials.py", "outputs/budongi_mvp_temp/tests/test_credential_server.py", "outputs/budongi_mvp_temp/tests/test_collection.py", "outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md", "outputs/budongi_mvp_temp/docs/specs/12_molit_collection_spec.md", "outputs/budongi_mvp_temp/docs/adr/ADR-004-local-api-credential-vault.md", "outputs/budongi_mvp_temp/docs/tasks/credential-alias-only.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "outputs/budongi_mvp_temp/README.md", "docs/sdd/traceability.json"]
acs = ["CRED-001-AC-01", "CRED-001-AC-02", "CRED-001-AC-03", "CRED-001-AC-05"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-alias-only.md#validation"
acs = ["CRED-001-AC-01", "CRED-001-AC-02", "CRED-001-AC-03", "CRED-001-AC-05"]

[[verification]]
command = "node --check outputs/budongi_mvp_temp/src/budongi/static/credentials.js; manual: 합성 보관함에서 별칭 등록·기존 키 별칭 수정·폴더 이동·키 입력 초기화·데스크톱/모바일 표시·콘솔 오류 확인"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-alias-only.md#validation"
acs = ["CRED-001-AC-01", "CRED-001-AC-03", "CRED-001-AC-05"]
```

2026-10-12 사용자 요청: 불완전한 연결 API 목록과 별칭이 겹쳐 키 종류를 잘못 판단하므로 전체 목록 또는 별칭만 사용하는 방식으로 수정. 별칭·폴더 관리로 통일한다. 실제 API 종류는 사용 작업에서 선택하고 키는 불투명한 ID로 지정한다. 실키 조회·수집·외부 호출은 수행하지 않는다.

## 원인과 범위

등록·수정 HTML의 고정 공급자 목록과 backend 목록이 다르고 신규 키에 공급자를 필수 요구했다. 기존 키의 폴더 수정도 지원하지 않았다. 화면의 연결 API 선택·열을 제거하고 신규 키에 중립 메타데이터를 적용한다. 기존 암호문·공급자 검사 호환성을 보존하고 폴더 이동은 재암호화 트랜잭션으로 처리한다. 수집 경로는 기존 공급자 메타데이터에서 키 종류를 판단하지 않고 명시한 ID를 사용한다. 기존 미커밋 수집 구현은 이 조회 변경 외에 보존한다.

## 완료 기준

- [x] CRED-001-AC-01 별칭만 등록·기존 키 폴더 이동·재시작·지정 ID 사용
- [x] CRED-001-AC-02 폴더 변경 암호문 재결합·실패 롤백·기존 fail-closed
- [x] CRED-001-AC-03 키 비노출·수정 창 입력 초기화
- [x] CRED-001-AC-05 합성 키로 검증하며 저장·수정의 외부 호출 없음

## validation

수정 전 회귀 테스트에서 공급자 없는 등록과 폴더 이동이 TypeError로 실패함을 확인했다. 수정 후 보관함/HTTP 테스트 36개 중 35개 통과·native WinCred 1개 skip, 수집 합성 테스트 10개 통과. 기존 공급자 메타데이터가 전월세인 한 키를 서비스별 ID 설정으로 세 서비스에서 재사용하는 합성 검증을 포함한다. 별칭/폴더에서 서비스 추론이나 실수집을 하지 않았다.

최종 `python -X utf8 scripts/verify_environment.py` 통과: 제품 테스트 95개 중 94개 통과·Windows native Credential Manager 1개는 현재 비대화형 로그온 세션 부재로 skip, SDD/팀 테스트 18개 통과, 합성 CLI smoke 통과. AES-GCM·기존 키 재시작 복호화·폴더 이동 재결합·잘못된 이동 롤백·비노출·fail-closed 회귀는 통과했으며 새로운 native OS 검증 완료를 주장하지 않는다. 최초 전체 검사의 기존 수집 Task 등록 누락은 해당 in_progress Task와 MOLIT Spec의 원장 연결을 보완해 해결했다. 해당 Task의 AC 상태·실수집 완료 상태는 변경하지 않았다.

gstack headless browser와 메모리 전용 master key·임시 SQLite를 사용했다. 공급자 선택 없이 합성 키를 등록하고 기존 키의 별칭을 바꿔 공공데이터 API 폴더로 이동했다. 목록 두 키의 별칭·폴더·마스킹과 폴더 개수 2/0을 확인했고 공급자 입력 요소 0개·키 입력 길이 0/0·닫힌 편집 창·콘솔 오류 없음이었다. 1280px 및 390px 화면을 캡처해 확인했다. 증거는 로컬 `.local_runtime/credential-alias-qa/`에 있으며 실키 조회·보관함 변경·외부 API 호출은 하지 않았다. 실행 중인 제품 서버는 새 Python 코드를 읽도록 재시작해야 한다.

운영 학습: 보관함 공급자 목록을 API 카탈로그로 해석하지 않는다. 서비스와 키 ID는 사용 작업에서 명시하고, 기존 provider_id는 암호문 호환성 데이터로 유지한다.

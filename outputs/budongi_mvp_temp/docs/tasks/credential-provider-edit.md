# TASK-CRED-PROVIDER-001 — 연결 API 수정

```toml
kind = "task"
id = "TASK-CRED-PROVIDER-001"
status = "verified"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md"]
scope = ["outputs/budongi_mvp_temp/src/budongi/credential_vault.py", "outputs/budongi_mvp_temp/src/budongi/credential_server.py", "outputs/budongi_mvp_temp/src/budongi/static/credentials.html", "outputs/budongi_mvp_temp/src/budongi/static/credentials.js", "outputs/budongi_mvp_temp/tests/test_credentials.py", "outputs/budongi_mvp_temp/tests/test_credential_server.py", "outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md", "outputs/budongi_mvp_temp/docs/tasks/credential-provider-edit.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["CRED-001-AC-01"]

[[verification]]
command = "python -m unittest discover -s tests -p test_credentials.py -v"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-provider-edit.md#validation"
acs = ["CRED-001-AC-01"]

[[verification]]
command = "python -m unittest discover -s tests -p test_credential_server.py -v"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-provider-edit.md#validation"
acs = ["CRED-001-AC-01"]
```

폴더는 사용자가 키를 묶는 위치이고, 연결 API는 해당 키가 사용할 연동 대상을 뜻한다. 지원 목록은 그대로 두되 저장된 키의 연결 대상을 등록 후에도 수정 가능하게 한다. 기존 키는 서버 내부에서 복호화 후 새 제공자 ID와 함께 다시 암호화하며 키 입력값은 응답에 포함하지 않는다.

## 완료 기준

- [x] CRED-001-AC-01 연결 API를 키별로 선택하고 저장 후에도 변경 가능

## validation

수정 전에는 보관함 API가 기존 연결 API를 바꾸는 인자를 받지 않았고 편집 화면에도 선택 항목이 없었다. 수정 후 `CredentialVaultTests.test_provider_can_be_changed_and_secret_is_reencrypted`와 `CredentialServerTests.test_api_provider_can_be_changed_through_edit_endpoint`를 포함한 저장소 테스트 14개 중 13개 통과·native WinCred 1개 skip, 서버 테스트 8개 통과. 암호문은 새 제공자 ID에 재결합되고 기존 제공자 ID로는 불러올 수 없음을 확인했다.

`node --check outputs/budongi_mvp_temp/src/budongi/static/credentials.js` 및 `python -X utf8 scripts/check_sdd.py --base origin/main` 통과. 로컬 합성 키 보관함 UI에서 편집 창의 `연결 API`를 Kakao Local에서 서울 열린데이터광장으로 바꾸어 저장했으며, 목록이 새 연결 API·기존 별칭·마스킹 상태로 갱신되고 키 입력 길이가 0인 것을 확인했다. 브라우저 콘솔 오류 없음. native Credential Manager round-trip은 기존 CRED-001 AC-02 미완료 상태를 유지한다.

# TASK-CREDENTIAL-LAUNCHER-001 — API 키 보관함 Windows EXE

```toml
kind = "task"
id = "TASK-CREDENTIAL-LAUNCHER-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md"]
scope = ["credential_launcher.py", "build_credentials_exe.ps1", "jipdam-credentials.exe", "README.md", "outputs/budongi_mvp_temp/README.md", "docs/tasks/credential-server-launcher.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["CRED-001-AC-01", "CRED-001-AC-03", "CRED-001-AC-05"]

[[verification]]
command = "not_run"
result = "not_run"
evidence = "docs/tasks/credential-server-launcher.md"
acs = ["CRED-001-AC-01", "CRED-001-AC-03", "CRED-001-AC-05"]
```

## Acceptance Criteria

- [ ] CRED-001-AC-01 EXE가 기존 사용자 프로필 보관함 서버를 시작하고 브라우저를 연다.
- [ ] CRED-001-AC-03 EXE 추가로 키 원문이 응답·로그·Git에 노출되지 않는다.
- [ ] CRED-001-AC-05 설정 UI에서 등록·저장 동작은 외부 API를 호출하지 않는다.

## 실행 결과

빌드와 로컬 화면 준비 확인 전.

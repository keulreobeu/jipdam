```toml
kind = "task"
id = "TASK-MAC-LAUNCHER-001"
status = "in_progress"
owner = "keulreobeu"
specs = ["outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md", "outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["jipdam-mac.command", "build_macos_app.sh", "build_credentials_exe.ps1", "build_server_exe.ps1", "server_launcher.py", "credential_launcher.py", "jipdam-server.exe", "jipdam-credentials.exe", "outputs/budongi_mvp_temp/pyproject.toml", "outputs/budongi_mvp_temp/src/budongi/credential_vault.py", "outputs/budongi_mvp_temp/tests/test_credentials.py", "outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md", "outputs/budongi_mvp_temp/docs/tasks/mac-launcher.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["CRED-001-AC-07", "CRED-001-AC-08", "CRED-001-AC-09"]
```

# TASK-MAC-LAUNCHER-001 — macOS 통합 실행기

## Acceptance criteria

- AC-07: macOS에서 `jipdam-mac.command`를 더블클릭하면 한 터미널 메뉴에서 전월세 서버 또는 API 키 보관함을 시작할 수 있다.
- AC-08: 자격증명 암호화 키는 macOS Keychain에만 저장하고, 보관함 DB는 사용자 Application Support 경로에 저장한다. Keychain 접근 실패 시 fail-closed한다.
- AC-09: `build_macos_app.sh`는 macOS에서 `집담.app`을 만들고 실행기를 호출한다. 실제 Mac에서 빌드·실행하지 않은 AC는 완료로 보고하지 않는다.

## Validation

- `python -X utf8 -m unittest test_credentials -v`: passed (18 tests, including mocked Keychain round-trip and macOS user-local path).
- Python source parsing and traceability JSON parsing: passed.
- `python -X utf8 scripts/verify_environment.py`: passed; SDD validation found 16 features, 92 ACs, 36 Tasks and 13 changed paths; 283 product tests, 35 team tests and model-free CLI smoke passed.
- `git diff --check`: passed. Windows PowerShell build scripts parse successfully.
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build_credentials_exe.ps1`: passed; created the executable with cryptography/openpyxl installed in the isolated build environment and bundled.
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build_server_exe.ps1`: passed; reused the dependency-complete build environment.
- `jipdam-server.exe --jipdam-child rental-mvp --help` and `jipdam-credentials.exe --jipdam-child credentials --help`: passed; both bundled executables loaded their CLI without a separate Python package installation.
- The rebuilt executables are 15,070,589 bytes (server) and 15,072,777 bytes (credentials); these updated binaries are included in the branch.
- 2026-10-22 user confirmed the macOS launcher runs normally. Native Keychain failure-path verification was not separately reported.
- `zsh -n jipdam-mac.command build_macos_app.sh`: not run on this Windows host.

## Status

macOS launcher normal execution was confirmed by the user. Both Windows EXEs were rebuilt and their bundled CLI/dependency load passed; this confirms they no longer require a separate target-PC Python package installation. Native macOS Keychain failure behavior remains unverified.

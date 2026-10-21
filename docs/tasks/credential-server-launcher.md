# TASK-CREDENTIAL-LAUNCHER-001 — API 키 보관함 Windows EXE

```toml
kind = "task"
id = "TASK-CREDENTIAL-LAUNCHER-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md"]
scope = ["jipdam-credentials.exe", "docs/tasks/credential-server-launcher.md"]
acs = ["CRED-001-AC-01", "CRED-001-AC-03", "CRED-001-AC-05"]

[[verification]]
command = "사용자 확인: 보관함 실행 EXE 정상 작동; 서울 열린데이터 광장 폴더의 자격 증명 2개 저장 및 암호문 복호화 가능 확인(키 값 미출력)"
result = "passed"
evidence = "사용자 확인 및 Windows 사용자 보관함 읽기 전용 점검"
acs = ["CRED-001-AC-01", "CRED-001-AC-03", "CRED-001-AC-05"]
```

## Acceptance Criteria

- [x] CRED-001-AC-01 EXE가 기존 사용자 프로필 보관함 서버를 시작하고 브라우저를 연다.
- [x] CRED-001-AC-03 자격 증명 원문을 응답·로그·Git에 노출하지 않는다.
- [x] CRED-001-AC-05 설정 UI의 등록·저장 동작은 외부 API를 호출하지 않는다.

## 실행 결과

Windows용 `jipdam-credentials.exe`를 생성했다. 사용자가 실행기 정상 동작을 확인했다. Windows 보관함의 `서울 열린데이터 광장` 폴더에 자격 증명 2개가 있고 두 암호문이 복호화 가능한 것을 읽기 전용으로 확인했다. 키 값은 화면·로그에 출력하지 않았다.

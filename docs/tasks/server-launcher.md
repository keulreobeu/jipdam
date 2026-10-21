# TASK-SERVER-LAUNCHER-001 — Windows 원클릭 서버 실행

```toml
kind = "task"
id = "TASK-SERVER-LAUNCHER-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["jipdam-server.exe", "docs/sdd/traceability.json", "docs/tasks/server-launcher.md"]
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14"]

[[verification]]
command = "사용자 확인: 서버 실행 EXE 정상 작동"
result = "passed"
evidence = "docs/tasks/server-launcher.md"
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14"]
```

## Acceptance Criteria

- [x] RENT-001-AC-12 루트 런처를 실행하면 서버 터미널이 열리고 Python 서버가 시작된다.
- [x] RENT-001-AC-13 준비가 확인되면 기본 브라우저가 선택된 loopback 포트를 연다.
- [x] RENT-001-AC-14 DB 미존재·서버 시작 실패를 사용자에게 표시하고 사용 방법을 안내한다.

## 실행 결과

Windows용 `jipdam-server.exe`를 생성했다. 사용자가 서버 실행기의 정상 작동을 확인했다.

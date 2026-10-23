# TASK-SERVER-LAUNCHER-001 — Windows 원클릭 서버 실행

```toml
kind = "task"
id = "TASK-SERVER-LAUNCHER-001"
status = "in_progress"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/10_rental_recommendation_spec.md"]
scope = ["server_launcher.py", "build_server_exe.ps1", "집담 서버 실행.ps1", "집담 서버 실행.exe", "jipdam-server.exe", "jipdam-server-v2.exe", "jipdam-server-v3.exe", "jipdam-server-v4.exe", "jipdam-server-v5.exe", "README.md", "docs/tasks/server-launcher.md", "docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14"]

[[verification]]
command = "not_run"
result = "not_run"
evidence = "docs/tasks/server-launcher.md"
acs = ["RENT-001-AC-12", "RENT-001-AC-13", "RENT-001-AC-14"]
```

## 범위

저장소 루트 또는 앱 폴더의 Windows EXE가 기존 Python MVP 서버를 시작하고 기본 브라우저에서 loopback 화면을 연다. 실행 데이터베이스는 기존 `outputs/budongi_mvp_temp/data/rental/serving/reviewed-20261020.sqlite3`를 읽기 전용 추천 경로로 사용한다. DB와 Python 앱 코드는 EXE에 복사하지 않는다.

## Acceptance Criteria

- [ ] RENT-001-AC-12 루트 또는 앱 폴더의 Windows 런처를 실행하면 서버 터미널이 열리고 Python 서버가 시작된다.
- [ ] RENT-001-AC-13 준비가 확인되면 기본 브라우저가 선택된 loopback 포트를 연다.
- [ ] RENT-001-AC-14 DB 미존재·서버 시작 실패를 사용자에게 표시하고 빌드/사용 방법을 README에 안내한다.

## 실행 결과

한글 `--name` 오류를 해결하기 위해 PyInstaller 내부 이름은 ASCII를 쓴다. 실행 파일 위치·현재 디렉터리·저장소 루트의 앱 경로를 검색하며, 기본 포트 충돌 시 8767~8796의 가용 포트를 사용한다. 터미널 표시와 서버 자식 프로세스 출력을 연결한다. DB read-only opener와 `canonical_rental_status`는 `status=ready`, 관측 238,620건을 확인했다. 실행 샌드박스에서는 loopback이 제한돼 HTTP 브라우저 검증은 하지 못했다.

# TASK-CRED-CI-001 — Windows CI 동시성 테스트 안정화

```toml
kind = "task"
id = "TASK-CRED-CI-001"
status = "verified"
owner = "Codex"
specs = ["outputs/budongi_mvp_temp/docs/specs/11_api_credential_vault_spec.md"]
scope = ["outputs/budongi_mvp_temp/tests/test_credential_regressions.py", "outputs/budongi_mvp_temp/docs/tasks/credential-vault-ci.md", "outputs/budongi_mvp_temp/docs/tasks/current.md", "docs/sdd/traceability.json"]
acs = ["CRED-001-AC-04", "CRED-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/verify_environment.py"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-vault-ci.md#validation"
acs = ["CRED-001-AC-04", "CRED-001-AC-06"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "outputs/budongi_mvp_temp/docs/tasks/credential-vault-ci.md#validation"
acs = ["CRED-001-AC-06"]
```

## 목표·범위

2026-10-07 사용자가 `codex/rental-recommendation`의 차단 해결을 요청했다. PR #2의 필수 Windows/Python 3.11 검사가 동시성 테스트 실패로 병합을 차단했다. GitHub 인증·관리 권한 문제는 아니었다.

기존 테스트는 쓰기 스레드를 2초만 기다린 뒤 실패했고, 임시 디렉터리 정리가 실행 중인 SQLite 파일에 접근해 WinError 32를 발생시켰다. SQLite의 잠금 대기 한도는 5초다. 합성 쓰기 COMMIT에 3초 지연을 주면 기존 `writer.is_alive()` 검사가 실패하는 것을 재현했다.

테스트를 이벤트로 조율하고, 읽기 작업의 성공·실패와 관계없이 쓰기 스레드 종료를 기다린다. DELETE는 읽기 잠금 아래 쓰기의 COMMIT 도달을, WAL은 두 조회 사이 쓰기 완료를 확인한다. WAL은 테스트용 합성 DB에서만 사용한다. 제품의 저장 방식·보안 계약·브랜치 보호는 변경하지 않는다.

## 완료 기준

- [x] CRED-001-AC-04 폴더 개수와 키 목록의 동일 읽기 스냅샷을 DELETE·WAL에서 검증하고 쓰기 완료 후 새 상태도 확인한다.
- [x] CRED-001-AC-06 Task·현재 작업·추적 원장을 연결하고 실제 검증 결과를 기록한다.

## validation

- 원본 실패: [Windows 3.11 CI](https://github.com/keulreobeu/jipdam/actions/runs/37599946987/job/112721587089).
- 원인 재현: 기존 테스트의 합성 쓰기 COMMIT 3초 지연 시 `True is not false`, 약 2.23초 후 쓰기 스레드가 실행 중이었다. 재현 도구는 스레드를 종료시킨 뒤 임시 DB를 정리했다.
- 수정 후 Windows/Python 3.11.9 집중 검사: `python -X utf8 -m unittest discover -s tests -p test_credential_regressions.py -v`(앱 디렉터리에서 실행), 11개 모두 통과.
- 동일 스냅샷 검사 20회 반복(각 DELETE·WAL), 모두 통과. 쓰기 스레드 시작을 3초 지연한 두 모드도 통과해 원래의 2초 종료 가정이 제거됨을 확인했다. 합성 키만 사용했다.
- 메모리에서 `list_state`의 읽기 BEGIN/COMMIT을 제거한 mutation 검사: WAL에서 기존 개수 0과 새 키 목록 1의 불일치를 잡아 실패했다. DELETE에서도 실패했다. 제품 소스는 변경하지 않았고, 원본 함수로 복원 후 정상 검사가 통과했다.
- `python -X utf8 scripts/verify_environment.py`: 앱 82개·루트 18개 총 100개 통과, 현재 사용자 세션의 합성 WinCred round-trip도 통과, 합성 CLI smoke 통과.
- `python -X utf8 scripts/check_sdd.py --base origin/main`: 4 features·29 AC·15 Tasks·53 changed paths 검사 통과. `git diff --check` 통과.
- 위 검증은 프로젝트 `.venv`의 Python 3.11.9·cryptography 50.0.2에서 실행했다. 원격 Windows/Linux와 Python 3.11/3.12 매트릭스 결과는 PR 검사에서 별도 확인한다.

## 결과·남은 조건

실제 API 호출·실데이터 수집·모델 평가·main 병합은 이 수정의 범위에 포함하지 않는다.

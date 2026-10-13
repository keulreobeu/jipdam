# Task — 현재 PC 프로젝트 환경 구성

```toml
kind = "task"
id = "TASK-ENV-002"
status = "verified"
owner = "Codex"
specs = ["docs/team_environment_spec.md", "docs/specs/sdd_workflow_spec.md"]
scope = ["docs/tasks/environment-setup-20261012.md", "docs/team_environment_validation.md", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/docs/tasks/current.md"]
acs = ["SDD-001-AC-03", "SDD-001-AC-05"]

[[verification]]
command = ". ./.local_runtime/activate.ps1; python -X utf8 scripts/bootstrap.py"
result = "passed"
evidence = "docs/team_environment_validation.md#environment-setup-2026-10-12"
acs = ["SDD-001-AC-03", "SDD-001-AC-05"]

[[verification]]
command = ".venv/Scripts/python.exe -m pip check; .venv/Scripts/jipdam.exe --help; .venv/Scripts/budongi.exe --help"
result = "passed"
evidence = "docs/team_environment_validation.md#environment-setup-2026-10-12"
acs = ["SDD-001-AC-05"]

[[verification]]
command = ". ./.local_runtime/activate.ps1; jipdam recommend --rental-db .local_runtime/rental-demo-20261012/serving.sqlite3 --snapshot-id synthetic_rental_demo_v1 --request .local_runtime/rental-demo-20261012/request.json --allow-synthetic"
result = "passed"
evidence = "docs/team_environment_validation.md#environment-setup-2026-10-12"
acs = ["SDD-001-AC-05"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "docs/team_environment_validation.md#environment-setup-2026-10-12"
acs = ["SDD-001-AC-03"]
```

## 목표·범위

설정 변경. 사용자의 2026-10-12 `이 프로젝트 환경구성 진행` 요청에 따라 README와 Team Environment Spec·ADR-002의 기존 설치 계약을 현재 Windows checkout에 적용한다. 기존 `.venv`와 editable 앱 설치를 확인하고, 누락된 Bun·고정 gstack·Chromium을 로컬에 설치한 뒤 기본 검증·CLI·브라우저 smoke를 실행한다.

설치 시작 시 Python 3.12.10, Node.js 24.18.0, Git for Windows와 `.venv`의 jipdam 0.1.0·cryptography 50.0.2는 존재했다. Bun 명령과 gstack source·생성 스킬·브라우저 runtime은 없었다. Bun과 세션 활성화 스크립트는 Git 제외 `.local_runtime/`에 두고 전역 PATH·PowerShell 프로필·Codex 설정을 변경하지 않는다.

제품 코드·데이터 계약, Docker·Ollama·모델 설치, 실데이터 수집·매칭·실제 Golden, 원격 게시·자동 업데이트는 범위 밖이다. 실제 수집·매칭 보류를 유지한다.

## 완료 기준

- [x] SDD-001-AC-03 로컬 구성과 결과를 영구 Task·추적 원장·현재 Task 및 검증 기록에 연결한다.
- [x] SDD-001-AC-05 가상환경 의존성·CLI, 모델 없는 기본 검증, 고정 gstack·고유 스킬 57개 및 Chromium smoke가 통과한다.

## 검증 기록

실행 결과는 [환경 검증 기록](../team_environment_validation.md)에 추가한다. 로컬 설치 로그와 브라우저 산출물은 `.local_runtime/`에 보존한다.

## 결과·남은 조건

완료. 기존 가상환경·editable 앱을 재사용하고 공식 SHA-256을 확인한 Bun 1.3.14를 프로젝트 로컬에 설치했다. 고정 gstack 1.91.9.0과 고유 스킬 57개, Chromium을 설치하고 전체 bootstrap exit 0을 확인했다. 최종 제품 테스트 82개·팀/SDD 테스트 18개가 skip 없이 통과했다. 합성 역사 조회와 브라우저 smoke, 합성 전월세 후보 2건·없는 DB 오류도 정상이다.

추가 QA에서 직접 Windows CLI의 stdout이 UTF-8이 아닌 현상을 확인했다. report-only QA를 종료한 뒤 환경 구성 작업에서 `.local_runtime/activate.ps1`에 `PYTHONUTF8=1`을 설정하고 동일 추천 명령을 재실행해 UTF-8 증거 캡처·JSON 해석·DB 불변을 확인했다. Git Bash의 no-profile helper 호출에는 셸 내부 `/usr/bin:/bin` PATH가 필요하며 검증 기록에 명령을 남겼다. 제품 코드·테스트는 변경하지 않았다.

사용자의 후속 질문에 따라 Docker와 Ollama는 필요할 때 설치하는 선택 구성으로 유지한다. 현재 기본 데이터 처리 환경은 준비됐지만 실제 수집·매칭 보류 해제와 GitHub 범위 예약·기록은 별도 절차이며 수집을 실행하지 않았다.

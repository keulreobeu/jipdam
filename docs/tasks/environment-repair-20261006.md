# Task — 환경 검수 누락 보완

```toml
kind = "task"
id = "TASK-ENV-001"
status = "verified"
owner = "Codex"
specs = ["docs/team_environment_spec.md", "docs/specs/sdd_workflow_spec.md"]
scope = ["docs/tasks/environment-repair-20261006.md", "docs/team_environment_validation.md", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/docs/tasks/current.md"]
acs = ["SDD-001-AC-03", "SDD-001-AC-05"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/verify_environment.py --gstack --browser"
result = "passed"
evidence = "docs/team_environment_validation.md#environment-repair-2026-10-06"
acs = ["SDD-001-AC-03", "SDD-001-AC-05"]

[[verification]]
command = "bunx playwright install chromium"
result = "passed"
evidence = "docs/team_environment_validation.md#environment-repair-2026-10-06"
acs = ["SDD-001-AC-05"]

[[verification]]
command = ".venv/Scripts/jipdam.exe --help; .venv/Scripts/budongi.exe --help; .venv/Scripts/python.exe -m pip check"
result = "passed"
evidence = "docs/team_environment_validation.md#environment-repair-2026-10-06"
acs = ["SDD-001-AC-05"]
```

## 목표·확정 근거

설정 변경. 사용자의 2026-10-06 요청 `검수에서 누락된 부분 다시 진행`에 따라 현재 PC의 bunx 누락을 보완하고 README의 선택 구성인 가상환경·editable CLI 설치를 완료한다. 기존 Team Environment Spec과 ADR-002의 로컬 설치 경로를 따른다.

검수에서 새 Windows PATH와 Git Bash 모두 bunx를 찾지 못했다. gstack setup은 Chromium 설치에 bunx를 호출한다. Bun 자체와 현재 Chromium은 실행되므로 기존 Bun의 설치 마무리 단계로 명령 연결을 복구하고 같은 실패 명령을 재실행한다.

변경 대상은 사용자 Bun 설치의 명령 연결, Git에서 제외된 `.venv/`, 이 Task와 검증 기록이다. 제품 코드·API·데이터 계약 변경, 실제 수집·매칭·Golden·모델 설치, gstack upgrade, 원격 작업은 포함하지 않는다. Docker/Ollama와 CSO의 선택형 런타임은 이번 완료 범위 밖이다.

## 완료 기준

- [x] SDD-001-AC-03 설정 변경·결과를 영구 Task와 선언한 문서 범위에 연결한다.
- [x] SDD-001-AC-05 이 Task의 로컬 범위에서 기본 환경 검증·합성 CLI·고정 gstack·브라우저 smoke가 통과한다. 기존 CI 계약을 변경하거나 새 원격 CI 실행을 주장하지 않는다.

추가 운영 확인: 새 Windows PATH 및 일반 Git Bash에서 bunx가 실행되고, `.venv`에서 jipdam/budongi help와 패키지 의존성 검사가 통과한다.

## 검증 기록

[검증 기록](../team_environment_validation.md#environment-repair-2026-10-06)에 결과·버전을 요약한다. 원본 stderr/stdout와 exit code는 `.local_runtime/gstack/qa-reports/environment-repair-20261006T045305Z/`의 001~003 capture로 보존했다. 001은 원래 실패했던 Windows PATH 명령의 재실행, 002는 새 Git Bash와 활성화한 가상환경, 003은 전체 모델 없는 검증이다.

## 결과·남은 조건

완료. 기존 Bun 1.4.2의 설치 마무리 명령이 bunx.exe 연결을 생성했다. 새 Windows PATH 및 Git Bash에서 bunx가 실행됐고, 프로젝트 Playwright 1.62.1의 Chromium 설치 명령도 exit 0이었다. Python 3.12.10 가상환경에 jipdam 0.1.0을 editable로 설치하고 두 CLI 및 pip check를 확인했다. 테스트 46개, 합성 CLI, 고정 gstack와 고유 스킬 57개, browser smoke가 통과했다.

외부 사용자 설치 디렉터리·가상환경·문서가 변경 대상이어서 단일 제품 모듈 freeze는 사용하지 않고 이 Task의 명시한 경로와 설치 작업에 한정했다. 제품 코드 변경에 해당하는 새 회귀 테스트 대신 원래 실패 명령을 같은 경계에서 재실행해 수정 전 exit 127, 수정 후 exit 0을 확인했다.

CSO C++ toolchain, Docker/Ollama·모델과 실제 데이터·Golden 평가는 별도 선택 조건이다. 이 Task의 완료는 해당 기능이나 실제 제품 평가의 완료를 의미하지 않는다.

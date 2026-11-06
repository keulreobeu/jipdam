# Task — Windows bootstrap 도구 탐지 보완

```toml
kind = "task"
id = "TASK-ENV-WIN-TOOLS-001"
status = "verified"
owner = "lwwde07"
specs = ["docs/team_environment_spec.md", "docs/specs/sdd_workflow_spec.md"]
scope = ["scripts/team_tools.py", "tests/test_team_setup.py", "docs/tasks/windows-bootstrap-tools.md", "docs/team_environment_validation.md", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/docs/tasks/current.md"]
acs = ["SDD-001-AC-03", "SDD-001-AC-05"]

[[verification]]
command = ".venv/Scripts/python -X utf8 scripts/bootstrap.py --host claude (Git Bash, PATH 우회 없음)"
result = "passed"
evidence = "docs/team_environment_validation.md#windows-bootstrap-tools-2026-11-06"
acs = ["SDD-001-AC-05"]

[[verification]]
command = ".venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --host claude (PowerShell, bun.exe가 PATH에 없음)"
result = "passed"
evidence = "docs/team_environment_validation.md#windows-bootstrap-tools-2026-11-06"
acs = ["SDD-001-AC-05"]

[[verification]]
command = ".venv/Scripts/python -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "docs/team_environment_validation.md#windows-bootstrap-tools-2026-11-06"
acs = ["SDD-001-AC-03"]
```

## 목표·범위·제외 범위

버그 수정. 사용자의 2026-11-06 요청 `환경구성 해줘`를 수행하던 중 Windows에서 두 실패가 재현됐고, 같은 날 사용자가 수정을 승인했다. 기존 [Team Environment Spec](../team_environment_spec.md)의 Windows Git Bash·Bun 설치 계약 안의 수정이며 계약 자체는 바꾸지 않는다.

- Git Bash 안에서 실행하면 `git`이 `mingw64/bin/git.exe`로 잡혀 Git Bash를 찾지 못했다.
- npm으로 설치한 Bun은 `bun.cmd` 셰임이라 `run(['bun', ...])`이 `WinError 2`로 실패했다.

변경 대상은 `scripts/team_tools.py`의 Git Bash 탐지와 `run()`의 실행 파일 해석, 회귀 테스트, 이 Task와 검증 기록이다. gstack lock·Bun 최소 버전 변경, 제품 코드·데이터 변경, 원격 작업은 포함하지 않는다.

GMS는 호출하지 않았다. 기록된 키 만료가 2026-10-16 18:00 KST로 작업일 이전이므로 만료 시 무생성 규칙을 따랐다.

## 완료 기준

- [x] SDD-001-AC-03 버그 수정과 결과를 이 영구 Task와 선언한 범위에 연결한다.
- [x] SDD-001-AC-05 이 Task의 로컬 범위에서 Git Bash와 PowerShell 모두 PATH 우회 없이 전체 bootstrap과 기본 검증·gstack·브라우저 smoke가 통과한다. 기존 CI 계약을 변경하거나 새 원격 CI 실행을 주장하지 않는다.

## 결과·남은 조건

완료. Git Bash와 PowerShell 모두 PATH 우회 없이 전체 bootstrap과 후속 검증이 exit 0으로 끝났다. 수정 전에는 같은 명령이 각각 `Install Git for Windows including Git Bash`와 `WinError 2`로 실패했다. 근거는 [검증 기록](../team_environment_validation.md#windows-bootstrap-tools-2026-11-06)에 있다.

Windows 이외 환경과 GitHub CI는 이 Task에서 실행하지 않았다. 회귀 테스트는 플랫폼 독립으로 작성했으므로 Ubuntu 결과는 PR CI에서 확인한다. 이 Task의 완료는 실제 모델·데이터 평가의 완료를 의미하지 않는다.

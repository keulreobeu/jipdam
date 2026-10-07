# TASK-CI-DEPS-001 — 모델 없는 CI Python 의존성 설치

```toml
kind = "task"
id = "TASK-CI-DEPS-001"
status = "verified"
owner = "keulreobeu"
specs = ["docs/team_environment_spec.md", "docs/specs/sdd_workflow_spec.md"]
scope = [".github/workflows/verify.yml", "README.md", "docs/tasks/ci-python-dependencies.md", "docs/team_environment_validation.md", "docs/sdd/traceability.json"]
acs = ["SDD-001-AC-05"]

[[verification]]
command = "temporary venv: python -m pip install -e outputs/budongi_mvp_temp; python -X utf8 scripts/bootstrap.py --app-only"
result = "passed"
evidence = "docs/tasks/ci-python-dependencies.md#validation"
acs = ["SDD-001-AC-05"]

[[verification]]
command = "python -X utf8 scripts/check_sdd.py --base origin/main"
result = "passed"
evidence = "docs/tasks/ci-python-dependencies.md#validation"
acs = ["SDD-001-AC-05"]

[[verification]]
command = "PR #2 수정 전 GitHub Actions model-free-checks matrix"
result = "failed"
evidence = "https://github.com/keulreobeu/jipdam/actions/runs/37598997366"
acs = ["SDD-001-AC-05"]

[[verification]]
command = "PR #2 수정 후 GitHub Actions model-free-checks matrix"
result = "passed"
evidence = "https://github.com/keulreobeu/jipdam/actions/runs/37599609319"
acs = ["SDD-001-AC-05"]
```

## 목표·계약

모델 없는 CI가 애플리케이션 모듈을 가져오기 전에 선언된 Python 앱 의존성을 설치한다. `--app-only`는 gstack·브라우저 설치 없이 실행한다. Ubuntu·Windows와 Python 3.11·3.12 조합에서 모두 통과해야 한다. [SDD-001](../specs/sdd_workflow_spec.md#sdd-001-ac-05-기본-검증과-시범-기능) 및 [팀 환경 계약](../team_environment_spec.md)을 따른다.

## 완료 기준

- [x] SDD-001-AC-05 CI가 검증 전에 editable 앱 패키지를 설치하고 네 OS/Python 조합이 모두 통과한다.

## Validation

PR #2 최초 실행은 앱 `pyproject.toml`에 선언된 `cryptography`가 깨끗한 runner에 설치되지 않아 실패했다. 제품 테스트가 시작되기 전에 앱 패키지와 의존성을 설치하도록 workflow를 보완했다. 로컬 전체 모델 없는 검증은 앱 의존성이 설치된 임시 환경에서 통과했다. 수정 후 GitHub Actions run 37599609319에서 Ubuntu/Windows × Python 3.11/3.12 네 job이 모두 성공했다.

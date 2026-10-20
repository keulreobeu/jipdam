# TASK-CLAUDE-GSTACK-001

```toml
kind = "task"
id = "TASK-CLAUDE-GSTACK-001"
status = "verified"
owner = "keulreobeu"
specs = ["docs/specs/claude_gstack_spec.md"]
scope = ["scripts/bootstrap.py", "scripts/register_gstack.py", "scripts/register_claude_gstack.py", "scripts/verify_environment.py", ".gitignore", "README.md", "AGENTS.md", "CLAUDE.md", "docs/gstack.md", "docs/team_environment_spec.md", "docs/specs/claude_gstack_spec.md", "docs/tasks/claude-gstack-support.md", "docs/team_environment_validation.md", "docs/sdd/traceability.json", "tests/test_host_gstack.py", "outputs/budongi_mvp_temp/docs/tasks/current.md"]
acs = ["CLAUDE-GSTACK-001-AC-01", "CLAUDE-GSTACK-001-AC-02", "CLAUDE-GSTACK-001-AC-03"]

[[verification]]
command = "python -X utf8 scripts/bootstrap.py --host claude --skip-verify; python -X utf8 scripts/register_claude_gstack.py --check"
result = "passed"
evidence = "docs/team_environment_validation.md#claude-gstack-2026-10-20"
acs = ["CLAUDE-GSTACK-001-AC-01", "CLAUDE-GSTACK-001-AC-03"]

[[verification]]
command = "python -X utf8 -m unittest discover -s tests -p test_host_gstack.py -v"
result = "passed"
evidence = "docs/team_environment_validation.md#claude-gstack-2026-10-20"
acs = ["CLAUDE-GSTACK-001-AC-01", "CLAUDE-GSTACK-001-AC-02", "CLAUDE-GSTACK-001-AC-03"]

[[verification]]
command = "python -X utf8 scripts/bootstrap.py --host codex --skip-verify; python -X utf8 scripts/register_gstack.py --check"
result = "passed"
evidence = "docs/team_environment_validation.md#host-specific-gstack-bootstrap-2026-10-20"
acs = ["CLAUDE-GSTACK-001-AC-03"]
```

- [x] CLAUDE-GSTACK-001-AC-01 Register 56 host-native Claude skills with no nested or duplicate manifests.
- [x] CLAUDE-GSTACK-001-AC-02 Keep helpers/state project-local; reject user-owned, foreign-marker and redirected output paths before writing.
- [x] CLAUDE-GSTACK-001-AC-03 Install either selected host, build the shared runtime, and remove only installer-owned registrations of the other host.

2026-10-20 제출 범위: 사용자가 Claude/Codex gstack 설치 지원만 main에 반영하도록 선택했다. Jira·부동산 데이터 변경은 포함하지 않는다. 독립 검토의 중첩 manifest, fresh Claude runtime 누락, 경로/소유 보호, helper 환경 경로 및 host별 upgrade 안내를 보완했다.
GMS는 기존 Task에 기록된 만료(2026-10-16 18:00 KST) 이후이며 이번 작업에서 새 유효 정책을 확인하지 않았으므로 호출하지 않았다. 키·공급자·예산을 우회하지 않았다.

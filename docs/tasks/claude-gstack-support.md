# TASK-CLAUDE-GSTACK-001

```toml
kind = "task"
id = "TASK-CLAUDE-GSTACK-001"
status = "in_progress"
owner = "keulreobeu"
specs = ["docs/specs/claude_gstack_spec.md"]
scope = ["scripts/bootstrap.py", "scripts/register_gstack.py", "scripts/register_claude_gstack.py", "scripts/verify_environment.py", ".gitignore", "README.md", "AGENTS.md", "CLAUDE.md", "docs/gstack.md", "docs/team_environment_spec.md", "docs/specs/claude_gstack_spec.md", "docs/tasks/claude-gstack-support.md", "docs/team_environment_validation.md", "docs/sdd/traceability.json"]
acs = ["CLAUDE-GSTACK-001-AC-01", "CLAUDE-GSTACK-001-AC-02", "CLAUDE-GSTACK-001-AC-03"]

[[verification]]
command = "python -X utf8 scripts/bootstrap.py --host claude --skip-verify; python -X utf8 scripts/register_claude_gstack.py --check"
result = "not_run"
evidence = "docs/team_environment_validation.md#host-specific-gstack-bootstrap-2026-10-20"
acs = ["CLAUDE-GSTACK-001-AC-01", "CLAUDE-GSTACK-001-AC-03"]

[[verification]]
command = "python -X utf8 scripts/register_gstack.py --check; call verify_gstack('codex'); count project .claude/skills/gstack*"
result = "passed"
evidence = "docs/team_environment_validation.md#host-specific-gstack-bootstrap-2026-10-20"
acs = ["CLAUDE-GSTACK-001-AC-03"]

[[verification]]
command = "python -X utf8 scripts/bootstrap.py --host codex --skip-verify"
result = "not_run"
evidence = "docs/team_environment_validation.md#host-specific-gstack-bootstrap-2026-10-20"
acs = ["CLAUDE-GSTACK-001-AC-03"]

[[verification]]
command = "Inspect registration paths and conflict checks in scripts/register_claude_gstack.py"
result = "passed"
evidence = "docs/team_environment_validation.md#claude-gstack-2026-10-20"
acs = ["CLAUDE-GSTACK-001-AC-02"]
```

- [x] CLAUDE-GSTACK-001-AC-01 Generate and register 56 host-native Claude skills from the locked gstack checkout.
- [x] CLAUDE-GSTACK-001-AC-02 Keep registration project-local, refuse user-owned collisions, and preserve Claude/Git permission boundaries.
- [ ] CLAUDE-GSTACK-001-AC-03 Install one selected host only and remove only marker-owned registrations for the other host when switching.

# TASK-JIRA-AUTO-001 — Codex·Claude Jira 작업 수명주기

```toml
kind = "task"
id = "TASK-JIRA-AUTO-001"
status = "verified"
owner = "keulreobeu"
specs = ["docs/specs/jira_task_lifecycle_spec.md"]
scope = [".mcp.json", "AGENTS.md", "README.md", "CLAUDE.md", "docs/sdd.md", "docs/specs/jira_task_lifecycle_spec.md", "docs/tasks/jira-task-lifecycle.md", "docs/team_environment_spec.md", "docs/team_environment_validation.md", ".agents/skills/jipdam-workflow/SKILL.md", "docs/sdd/traceability.json", "outputs/budongi_mvp_temp/docs/tasks/current.md"]
acs = ["JIRA-AUTO-001-AC-01", "JIRA-AUTO-001-AC-02", "JIRA-AUTO-001-AC-03", "JIRA-AUTO-001-AC-04"]

[[verification]]
command = "Focused check: parse .mcp.json and traceability JSON; verify TASK-JIRA-AUTO-001 scope/AC registration and Codex/Claude instructions; git diff --check"
result = "passed"
evidence = "docs/team_environment_validation.md#jira-task-lifecycle-2026-10-20"
acs = ["JIRA-AUTO-001-AC-01", "JIRA-AUTO-001-AC-02", "JIRA-AUTO-001-AC-03", "JIRA-AUTO-001-AC-04"]
```

Jira: [KAN-4](https://kwulreobeu.atlassian.net/browse/KAN-4)

## Goal, scope, and approval

Implement the user's 2026-10-20 request to have Codex and Claude Code track repository implementation/configuration tasks in Jira and close them only after verification. The approved behavior is defined in [JIRA-AUTO-001](../specs/jira_task_lifecycle_spec.md). No product code or member-specific assignments are part of this task.

## Completion criteria

- [x] JIRA-AUTO-001-AC-01 Create or link the Jira issue before implementation, report its key, mark it in-progress, and label the host.
- [x] JIRA-AUTO-001-AC-02 Close only verified work; keep blocked/incomplete work open.
- [x] JIRA-AUTO-001-AC-03 Configure/document Codex and Claude Code Jira access and OAuth.
- [x] JIRA-AUTO-001-AC-04 Preserve assignee, failure, and issue-scope boundaries.

## Verification record

The full `python -X utf8 scripts/check_sdd.py` command was attempted but is currently blocked by an unrelated pre-existing edit in `outputs/budongi_mvp_temp/docs/tasks/rental-real-data.md`: its second verification `result` contains prose instead of one of `passed`, `failed`, or `not_run`. That user change was left untouched. Focused checks for this Task passed.

# Jira Task Lifecycle Spec

```toml
kind = "spec"
id = "JIRA-AUTO-001"
status = "approved"
owner = "keulreobeu"
revision = 1
approved_by = "user"
approved_at = "2026-10-20"
approval_ref = "Codex thread request to automatically create and close Jira work items for Codex or Claude Code tasks"
```

## Goal and scope

Repository implementation, bug-fix, documentation, configuration, and validation work requested for the Jipdam project is tracked in the `KAN` Jira project, regardless of whether Codex or Claude Code performs it. This is an agent workflow contract, not a product runtime feature.

## JIRA-AUTO-001-REQ-01 Start a tracked work item

Before changing repository files or applying an external configuration, the agent searches for a clearly matching open work item or creates one Jira `작업` issue in `KAN`. It transitions the linked issue to in-progress when the project workflow offers that transition, records the issue key in its progress updates, and adds an `agent-codex` or `agent-claude` label to identify the host. Pure questions, explanations, planning without execution, and read-only review do not need a ticket.

### JIRA-AUTO-001-AC-01

For qualifying work, a Jira issue exists before implementation starts and its key is recorded. Use the user-provided issue when one is explicitly identified. Avoid duplicate tickets when a matching open issue is clearly identified. Mark it in-progress when possible and identify the coding host with a label.

## JIRA-AUTO-001-REQ-02 Complete only verified work

The agent transitions the linked issue to the project's completed status only after all requested changes are done and their relevant checks pass. If work is partial, blocked, or checks fail, the agent leaves the issue open and reports its state. Closing a ticket does not authorize merge, push, deployment, data collection, or other separately governed actions.

### JIRA-AUTO-001-AC-02

Completed work is closed in Jira after verification; incomplete or blocked work remains open with an accurate status and explanation.

## JIRA-AUTO-001-REQ-03 Use authorized host connections

Codex uses the connected Atlassian Jira integration. Claude Code uses the project-scoped official Atlassian Remote MCP configuration in `.mcp.json` and the user's OAuth session. The first Claude Code session must complete the `/mcp` authentication/approval flow. Do not put tokens or passwords in the repository or use shell/API-token fallbacks.

### JIRA-AUTO-001-AC-03

The repository provides the official Atlassian MCP endpoint for Claude Code, and project instructions explain one-time OAuth setup and the shared create/link/complete workflow for Codex and Claude Code.

## JIRA-AUTO-001-REQ-04 Preserve assignment and authorization boundaries

Do not infer an assignee from the agent, requester, or recent Jira activity. Set an assignee only when the user identifies one or an existing issue already has one. If Jira is unavailable or issue creation fails, report the failure before editing and ask whether to proceed without tracking. Jira transitions update only the task linked to the current request.

### JIRA-AUTO-001-AC-04

The workflow does not invent assignees, does not start untracked changes after Jira creation failure without user direction, and does not close unrelated work items.

## Related

- `docs/sdd.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.agents/skills/jipdam-workflow/SKILL.md`
- Official Atlassian MCP setup: <https://support.atlassian.com/atlassian-ai-gateway/docs/get-started-with-the-atlassian-remote-mcp-server/>

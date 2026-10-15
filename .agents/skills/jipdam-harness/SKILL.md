---
name: jipdam-harness
description: Run or resume the portable Jipdam developer harness with selective native roles, evidence and offline Mock budgets.
---

Read jipdam-workflow and current AGENTS/SDD first. Contracts and CLI are in
outputs/budongi_mvp_temp/docs/harness/README.md; user directions override this workflow.

1. Master maps the request to a permanent SDD Task and explicit kind: direct, bug, feature or audit.
   For a short explanation no harness run or subagent is necessary. For tiny code use direct:
   Master implements, Evaluator verifies. Do not force all roles.
2. Create a JSON task with task_id/kind/objective/scope_paths/acceptance_criteria.
   Run `python -X utf8 scripts/agent_harness.py new-task --request PATH` then
   `run --task ID --host codex`. Store the job under ignored .local_runtime/harness/.
3. Dispatch only the claimed role using native delegation. Prefer jipdam_planner, jipdam_engineer,
   jipdam_reviewer, jipdam_evaluator if actually discovered. Pass the complete job, Spec/Task
   and prohibited actions. Models inherit host settings. If custom roles are unavailable, use
   a supported generic native agent with role instructions; record fallback and actual native ID.
4. At most two native children may be active. No overlapping writer scopes; independent read-only
   reviews may overlap. This host rule supplements the DB claim limit. Wait for actual completion.
5. Inspect files, hashes and real test output. Build result schema v1; token_usage is null if
   unavailable. Submit with `submit --job PATH --result PATH`, then run the next queued stage.
6. Checkpoint at stage boundaries. On user stop call stop and interrupt the native worker too.
   Resume/context restores DB state. Use --recover-running only after confirming the old worker
   is dead; a rotated lease fences late results, not already-running tools.
7. Keep credentials/raw DBs/data out of jobs/results. Gateway is Mock-only. Existing gms-work
   quote/count can cost credits: use it only under the latest explicit user authorization and its
   existing vault/budget/reserve controls. Never bypass or increase limits. No automatic push/merge,
   destructive command or new collection follows from harness execution.
8. Record actual agents/files/commands/AC/token uncertainty in permanent Task/validation.
   Common JSON/SQLite supports manual Claude/Antigravity/CLI handoff; native registration and
   APIs require real smoke. Never invent CLI flags, auto-install hooks or reconfigure providers.

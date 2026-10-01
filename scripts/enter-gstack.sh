#!/usr/bin/env bash
# Source this file before calling the runtime directly from Bash.
_team_workspace="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
export GSTACK_ROOT="$_team_workspace/.local_runtime/tooling/.agents/skills/gstack"
export GSTACK_HOME="$_team_workspace/.local_runtime/gstack"
export GSTACK_PLAN_DIR="$_team_workspace/.local_runtime/gstack/plans"
export PLAYWRIGHT_BROWSERS_PATH="$_team_workspace/.local_runtime/playwright"
export BROWSE_STATE_FILE="$_team_workspace/.local_runtime/gstack/browser/browse.json"
unset _team_workspace

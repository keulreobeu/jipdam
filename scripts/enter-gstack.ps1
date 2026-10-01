# Dot-source this file when running gstack helpers directly in PowerShell.
$taskWorkspace = Split-Path -Parent $PSScriptRoot
$env:GSTACK_ROOT = (Join-Path $taskWorkspace '.local_runtime/tooling/.agents/skills/gstack').Replace('\', '/')
$env:GSTACK_HOME = (Join-Path $taskWorkspace '.local_runtime/gstack').Replace('\', '/')
$env:GSTACK_PLAN_DIR = (Join-Path $taskWorkspace '.local_runtime/gstack/plans').Replace('\', '/')
$env:PLAYWRIGHT_BROWSERS_PATH = (Join-Path $taskWorkspace '.local_runtime/playwright').Replace('\', '/')
$env:BROWSE_STATE_FILE = (Join-Path $taskWorkspace '.local_runtime/gstack/browser/browse.json').Replace('\', '/')

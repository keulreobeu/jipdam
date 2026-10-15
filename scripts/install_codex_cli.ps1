# Install the official CLI; do not change Codex credentials or provider configuration.
$ErrorActionPreference = 'Stop'
& npm.cmd install --global @openai/codex
if ($LASTEXITCODE -ne 0) { throw 'Codex CLI npm installation failed.' }
$taskNpmPrefix = (& npm.cmd config get prefix).Trim()
& (Join-Path $taskNpmPrefix 'codex.cmd') --version
if ($LASTEXITCODE -ne 0) { throw 'Codex CLI version check failed.' }

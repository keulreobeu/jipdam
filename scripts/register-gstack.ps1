$ErrorActionPreference = 'Stop'
& python -X utf8 (Join-Path $PSScriptRoot 'register_gstack.py') @args
if ($LASTEXITCODE -ne 0) { throw "Skill registration failed: exit $LASTEXITCODE" }

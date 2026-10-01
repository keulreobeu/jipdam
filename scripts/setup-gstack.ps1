# The Python bootstrap also works on Linux and macOS.
$ErrorActionPreference = 'Stop'
& python -X utf8 (Join-Path $PSScriptRoot 'bootstrap.py') @args
if ($LASTEXITCODE -ne 0) { throw "Team setup failed: exit $LASTEXITCODE" }

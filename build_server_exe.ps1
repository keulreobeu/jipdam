$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtime = Join-Path $workspace '.local_runtime\server-launcher'
$python = Get-Command python -ErrorAction Stop

New-Item -ItemType Directory -Force -Path $runtime | Out-Null
& $python.Source -m pip install --disable-pip-version-check --target $runtime 'pyinstaller>=6.10,<7'
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller 설치에 실패했습니다.' }

$env:PYTHONPATH = $runtime
& $python.Source -m PyInstaller --noconfirm --clean --onefile --console `
    --name 'jipdam-server-v5' `
    --distpath $workspace `
    --workpath (Join-Path $runtime 'build') `
    --specpath $runtime `
    (Join-Path $workspace 'server_launcher.py')
if ($LASTEXITCODE -ne 0) { throw '서버 실행 EXE 빌드에 실패했습니다.' }

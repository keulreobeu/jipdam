$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$app = Join-Path $workspace 'outputs\budongi_mvp_temp'
$runtime = Join-Path $workspace '.local_runtime\server-launcher'
$python = Get-Command python -ErrorAction Stop
$buildPython = Join-Path $runtime 'venv\Scripts\python.exe'

New-Item -ItemType Directory -Force -Path $runtime | Out-Null
if (-not (Test-Path $buildPython)) {
    & $python.Source -m venv (Join-Path $runtime 'venv')
    if ($LASTEXITCODE -ne 0) { throw '빌드용 Python 환경을 만들지 못했습니다.' }
}
& $buildPython -m pip install --disable-pip-version-check -e $app 'pyinstaller>=6.10,<7'
if ($LASTEXITCODE -ne 0) {
    throw 'PyInstaller와 집담 서버 의존성을 설치하지 못했습니다.'
}

$env:PYTHONPATH = Join-Path $app 'src'
& $buildPython -m PyInstaller --noconfirm --clean --onefile --console `
    --name 'jipdam-credentials' `
    --paths (Join-Path $app 'src') `
    --collect-all budongi `
    --distpath $workspace `
    --workpath (Join-Path $runtime 'credentials-build') `
    --specpath $runtime `
    (Join-Path $workspace 'credential_launcher.py')
if ($LASTEXITCODE -ne 0) { throw 'API 키 보관함 EXE 빌드에 실패했습니다.' }

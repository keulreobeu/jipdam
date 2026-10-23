$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$app = Join-Path $workspace 'outputs\budongi_mvp_temp'
$database = Join-Path $app 'data\rental\serving\reviewed-20261020.sqlite3'
$url = 'http://127.0.0.1:8766/'

if (-not (Test-Path -LiteralPath $database -PathType Leaf)) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("전월세 데이터베이스를 찾을 수 없습니다.`n$database", '집담 서버 실행') | Out-Null
    exit 1
}

try { Invoke-WebRequest -Uri ($url + 'api/status') -TimeoutSec 1 -UseBasicParsing | Out-Null }
catch {
    $env:PYTHONPATH = Join-Path $app 'src'
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue).Source }
    if (-not $python) {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show('Python 3.11 이상을 설치한 뒤 다시 실행해 주세요.', '집담 서버 실행') | Out-Null
        exit 1
    }
    Start-Process -FilePath $python -ArgumentList @('-X','utf8','-m','budongi.cli','rental-mvp','--database',$database,'--no-browser','--port','8766') -WorkingDirectory $app -WindowStyle Hidden
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 500
        try { Invoke-WebRequest -Uri ($url + 'api/status') -TimeoutSec 1 -UseBasicParsing | Out-Null; $ready = $true; break }
        catch { }
    }
    if (-not $ready) {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show('서버를 시작하지 못했습니다. Python 앱 의존성이 설치되어 있는지 확인해 주세요.', '집담 서버 실행') | Out-Null
        exit 1
    }
}
Start-Process $url

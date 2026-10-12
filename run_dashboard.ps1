param([int]$Port = 8501)

$ErrorActionPreference = 'Stop'
$dashboardPython = Join-Path $PSScriptRoot '.venv-dashboard/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $dashboardPython)) {
    throw 'Create the dashboard environment first: python -m venv .venv-dashboard; ./.venv-dashboard/Scripts/python.exe -m pip install -r requirements-dashboard.txt'
}
Push-Location $PSScriptRoot
try {
    & $dashboardPython -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port $Port --server.headless true
    $dashboardExit = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $dashboardExit

param([ValidateSet('demo','network','dashboard','test','train','compare')][string]$Task = 'demo')
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$localRuntime = Join-Path $projectRoot '..\..\work\runtime\python\python.exe'
$venvRuntime = Join-Path $projectRoot '.venv\Scripts\python.exe'
$projectRuntime = Join-Path $projectRoot '.runtime\python.exe'
if (Test-Path -LiteralPath $venvRuntime) { $pythonRunner = $venvRuntime }
elseif (Test-Path -LiteralPath $projectRuntime) { $pythonRunner = $projectRuntime }
elseif (Test-Path -LiteralPath $localRuntime) { $pythonRunner = $localRuntime }
else { $pythonRunner = (Get-Command python -ErrorAction Stop).Source }
Push-Location $projectRoot
try {
    $env:MPLCONFIGDIR = Join-Path $projectRoot '.cache\matplotlib'
    $env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = 'false'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    if ($Task -eq 'dashboard') {
        & $pythonRunner -m streamlit run dashboard.py --server.address 127.0.0.1
    } elseif ($Task -eq 'test') {
        & $pythonRunner -m pytest tests -q
    } else {
        & $pythonRunner -X utf8 run.py $Task
    }
    if ($LASTEXITCODE -ne 0) { throw "Project command exited with code $LASTEXITCODE" }
} finally { Pop-Location }

param([string]$Python = "python", [string]$Scenario = "local_background")
$ErrorActionPreference = "Stop"
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    & $Python -m qkd_monitor demo --scenario $Scenario --seed 42 --out results/demo
    if ($LASTEXITCODE -ne 0) { throw "Demo failed with exit code $LASTEXITCODE" }
    Write-Host "Open results/demo/report.html to inspect the report."
} finally {
    Pop-Location
}

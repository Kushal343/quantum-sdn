param([string]$Python = "python", [int]$Seeds = 30)
$ErrorActionPreference = "Stop"
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    & $Python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
    & $Python -m qkd_monitor benchmark --seed 1000 --seeds $Seeds --out results/benchmark
    if ($LASTEXITCODE -ne 0) { throw "Benchmark failed" }
    Write-Host "Open results/benchmark/report.html to inspect the study."
} finally {
    Pop-Location
}

#!/usr/bin/env pwsh
# PowerShell validation wrapper for Windows

param(
    [switch]$Test = $false
)

$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot

Write-Host "=== Python Syntax Check ===" -ForegroundColor Cyan
$allPassed = $true

foreach ($file in Get-ChildItem src/*.py) {
    Write-Host "  $($file.Name) " -NoNewline
    $output = python -m py_compile $file.FullName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK" -ForegroundColor Green
    } else {
        Write-Host "FAILED" -ForegroundColor Red
        Write-Host "    $output" -ForegroundColor Red
        $allPassed = $false
    }
}

if ($Test) {
    Write-Host ""
    Write-Host "=== Running Self-Tests ===" -ForegroundColor Cyan
    python src/main.py --test
    if ($LASTEXITCODE -ne 0) {
        $allPassed = $false
    }
}

Write-Host ""
if ($allPassed) {
    Write-Host "All validations passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Validation failed!" -ForegroundColor Red
    exit 1
}

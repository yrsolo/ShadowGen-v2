$ErrorActionPreference = "Stop"

Write-Host "Running docs check..."
powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1

Write-Host "Running tests..."
python -m pytest

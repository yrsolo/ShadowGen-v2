$ErrorActionPreference = "Stop"

$requiredFiles = @(
  "README.md",
  "AGENTS.md",
  "docs/README.md",
  "agent/OPERATING_CONTRACT.md",
  "work/now/current-task.md",
  "work/now/plan.md",
  "work/now/evidence.md",
  "apps/api/src/main.py"
)

$missing = $requiredFiles | Where-Object { -not (Test-Path $_) }

if ($missing.Count -gt 0) {
  Write-Error ("Missing required files: " + ($missing -join ", "))
}

Write-Host "Docs check passed"

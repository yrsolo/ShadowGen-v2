$ErrorActionPreference = "Stop"

$requiredFiles = @(
  "README.md",
  "AGENTS.md",
  "docs/README.md",
  "agent/OPERATING_CONTRACT.md",
  "work/now/current-task.md",
  "work/now/plan.md",
  "work/now/evidence.md",
  "apps/api/src/shadowgen_api/main.py",
  "apps/worker/src/shadowgen_worker/main.py",
  "packages/contracts/src/shadowgen_contracts/__init__.py",
  "packages/application/src/shadowgen_application/__init__.py",
  "packages/pipeline/src/shadowgen_pipeline/__init__.py",
  "packages/adapters/src/shadowgen_adapters/__init__.py"
)

$missing = $requiredFiles | Where-Object { -not (Test-Path $_) }

if ($missing.Count -gt 0) {
  Write-Error ("Missing required files: " + ($missing -join ", "))
}

Write-Host "Docs check passed"

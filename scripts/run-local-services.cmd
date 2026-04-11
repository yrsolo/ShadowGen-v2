@echo off
setlocal

cd /d "%~dp0.."

echo [ShadowGen] Starting local services...

if not exist ".venv\Scripts\python.exe" (
  echo [ShadowGen] .venv is missing. Run scripts\install-local-deps.cmd first.
  exit /b 1
)

if not exist "apps\web\node_modules" (
  echo [ShadowGen] Web dependencies are missing. Run scripts\install-local-deps.cmd first.
  exit /b 1
)

start "ShadowGen API" cmd /k "cd /d %CD% && .\.venv\Scripts\python.exe tools\dev\run_local.py"
start "ShadowGen Worker" cmd /k "cd /d %CD% && .\.venv\Scripts\python.exe -m shadowgen_worker.main"
start "ShadowGen Web" cmd /k "cd /d %CD%\apps\web && npm run dev"

echo.
echo [ShadowGen] Local services started.
echo API:  http://localhost:8000/docs
echo WEB:  http://localhost:3000
echo DIAG: http://localhost:8000/v1/system/diagnostics

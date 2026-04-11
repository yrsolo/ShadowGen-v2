@echo off
setlocal

cd /d "%~dp0.."

echo [ShadowGen] Starting local worker against cloud services...

if not exist ".venv\Scripts\python.exe" (
  echo [ShadowGen] .venv is missing. Run scripts\install-local-deps.cmd first.
  exit /b 1
)

if not exist ".env.shadowgen" (
  echo [ShadowGen] .env.shadowgen is missing.
  echo [ShadowGen] Create it first or copy from .env.shadowgen.example.
  exit /b 1
)

echo [ShadowGen] Using config from %CD%\.env.shadowgen
echo [ShadowGen] Worker will consume YMQ jobs and use Object Storage state.
echo [ShadowGen] Worker control UI: http://localhost:8081
echo [ShadowGen] Worker control JSON: http://localhost:8081/api/status
echo.

call .\.venv\Scripts\python.exe -m shadowgen_worker.main
exit /b %errorlevel%

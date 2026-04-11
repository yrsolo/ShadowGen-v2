@echo off
setlocal

cd /d "%~dp0.."

if not exist ".env.shadowgen" (
  echo [ShadowGen] .env.shadowgen is missing. Copy .env.shadowgen.example and fill Yandex credentials first.
  exit /b 1
)

echo [ShadowGen] Starting api/web containers...
docker compose -f docker-compose.local.yml up --build -d
if errorlevel 1 exit /b 1

echo.
echo [ShadowGen] Containers started.
echo API:  http://localhost:8000/docs
echo WEB:  http://localhost:3000
echo.
echo [ShadowGen] Start local worker separately:
echo .\.venv\Scripts\python.exe -m shadowgen_worker.main


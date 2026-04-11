@echo off
setlocal
setlocal EnableDelayedExpansion

cd /d "%~dp0.."

echo [ShadowGen] Starting worker container against cloud services...

if not exist ".env.shadowgen" (
  echo [ShadowGen] .env.shadowgen is missing.
  echo [ShadowGen] Create it first or copy from .env.shadowgen.example.
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo [ShadowGen] Docker is not available. Start Docker Desktop first.
  exit /b 1
)

echo [ShadowGen] Building worker image...
docker build -f apps\worker\Dockerfile -t shadowgen-worker-local .
if errorlevel 1 (
  echo [ShadowGen] Failed to build worker image.
  exit /b 1
)

set "LEGACY_ML_BASE_URL="
for /f "usebackq tokens=1,* delims==" %%A in (".env.shadowgen") do (
  if /I "%%~A"=="LEGACY_ML_BASE_URL" set "LEGACY_ML_BASE_URL=%%~B"
)

set "DOCKER_ADD_HOST_ARG="
if defined LEGACY_ML_BASE_URL (
  for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "$url = [Uri]$env:LEGACY_ML_BASE_URL; $url.Host"`) do (
    set "LEGACY_ML_HOST=%%~H"
  )
  for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "try { $url = [Uri]$env:LEGACY_ML_BASE_URL; $hostName = $url.Host; if ($hostName -match '^\d{1,3}(\.\d{1,3}){3}$') { $hostName } else { (Resolve-DnsName -Name $hostName -Type A -ErrorAction Stop | Select-Object -First 1 -ExpandProperty IPAddress) } } catch { '' }"`) do (
    set "LEGACY_ML_HOST_IP=%%~I"
  )
  if defined LEGACY_ML_HOST if defined LEGACY_ML_HOST_IP (
    echo [ShadowGen] Resolved ML host !LEGACY_ML_HOST! to !LEGACY_ML_HOST_IP! for the container.
    set "DOCKER_ADD_HOST_ARG=--add-host !LEGACY_ML_HOST!:!LEGACY_ML_HOST_IP!"
  )
)

for /f %%i in ('docker ps -aq --filter "name=^shadowgen-worker$"') do (
  echo [ShadowGen] Removing previous worker container...
  docker rm -f %%i >nul 2>&1
)

echo [ShadowGen] Running worker container with .env.shadowgen
echo [ShadowGen] Worker control UI: http://localhost:8081
echo [ShadowGen] Worker control JSON: http://localhost:8081/api/status
docker run --rm ^
  --name shadowgen-worker ^
  --env-file .env.shadowgen ^
  !DOCKER_ADD_HOST_ARG! ^
  -e WORKER_SELF_MANAGE_ENABLED=true ^
  -e WORKER_CONTAINER_NAME=shadowgen-worker ^
  -e WORKER_IMAGE_TAG=shadowgen-worker-local ^
  -e WORKER_WORKSPACE_MOUNT_DEST=/workspace ^
  -e WORKER_CONTROL_HOST=0.0.0.0 ^
  -e WORKER_CONTROL_PORT=8081 ^
  -e WORKER_CONTROL_HOST_PORT=8081 ^
  -p 8081:8081 ^
  -v "%CD%:/workspace" ^
  -v "//var/run/docker.sock:/var/run/docker.sock" ^
  shadowgen-worker-local
exit /b %errorlevel%

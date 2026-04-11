@echo off
setlocal

cd /d "%~dp0.."

echo [ShadowGen] Installing local dependencies...

if not exist ".env.shadowgen" (
  echo [ShadowGen] .env.shadowgen not found, copying from .env.shadowgen.example
  copy /Y ".env.shadowgen.example" ".env.shadowgen" >nul
)

if not exist ".venv" (
  echo [ShadowGen] Creating local virtual environment...
  call python -m venv .venv
  if errorlevel 1 goto :fail
)

echo [ShadowGen] Installing Python dependencies into .venv...
call .\.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :fail
call .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :fail
call .\.venv\Scripts\python.exe -m pip install -e .
if errorlevel 1 goto :fail

echo [ShadowGen] Installing web dependencies...
pushd "apps\web"
call npm install
if errorlevel 1 (
  popd
  goto :fail
)
popd

echo [ShadowGen] Local dependencies installed successfully.
echo PYTHON: %CD%\.venv\Scripts\python.exe
goto :eof

:fail
echo [ShadowGen] Failed to install local dependencies.
exit /b 1

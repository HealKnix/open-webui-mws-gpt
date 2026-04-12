@echo off
if "%OPEN_WEBUI_SKIP_POSTINSTALL%"=="1" (
    echo Skipping postinstall sync.
    exit /b 0
)
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo uv not found, installing...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
)
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set NODE_OPTIONS=--max-old-space-size=4096
uv sync
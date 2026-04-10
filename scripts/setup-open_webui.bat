@echo off
if "%OPEN_WEBUI_SKIP_POSTINSTALL%"=="1" (
    echo Skipping postinstall sync.
    exit /b 0
)
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
pip install uv && uv sync
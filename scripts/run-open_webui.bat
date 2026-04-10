@echo off
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
uv run uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload
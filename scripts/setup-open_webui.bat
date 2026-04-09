@echo off
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
py -m venv .venv && .venv\Scripts\activate && pip install -r backend/requirements.txt && pip install open-webui && python.exe -m pip install --upgrade pip
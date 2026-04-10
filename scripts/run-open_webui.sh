#!/bin/bash
uv run uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload
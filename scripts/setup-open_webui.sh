#!/bin/bash

python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt && pip install open-webui && python.exe -m pip install --upgrade pip
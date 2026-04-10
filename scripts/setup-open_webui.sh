#!/bin/bash
if [ "$OPEN_WEBUI_SKIP_POSTINSTALL" = "1" ]; then
    echo "Skipping postinstall sync."
    exit 0
fi
pip install uv && uv sync
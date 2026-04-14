#!/bin/bash
if [ "$OPEN_WEBUI_SKIP_POSTINSTALL" = "1" ]; then
    echo "Skipping postinstall sync."
    exit 0
fi
# Check if uv is installed, if not, install it via standalone script
if ! command -v uv &> /dev/null; then
    echo "uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Ensure uv is in the path for the current session
    export PATH="$HOME/.local/bin:$PATH"
fi
export NODE_OPTIONS="--max-old-space-size=4096"
uv sync
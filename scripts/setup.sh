#!/usr/bin/env bash
# Agent Platform — Guided Setup
# Run: bash scripts/setup.sh

set -e

echo "============================================================"
echo "  Agent Platform — Setup"
echo "============================================================"
echo

# 1. Check Python
echo "[1/6] Checking Python version..."
if ! command -v python3 &>/dev/null; then
    echo "  ERROR: Python 3 not found. Install Python 3.13+: https://python.org/downloads/"
    exit 1
fi
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Found Python $PY_VERSION"

# 2. Check/install uv
echo "[2/6] Checking uv..."
if ! command -v uv &>/dev/null; then
    echo "  uv not found. Installing..."
    pip install uv
fi
echo "  uv is available"

# 3. Install dependencies
echo "[3/6] Installing dependencies..."
uv sync
echo "  Dependencies installed"

# 4. Create .env if needed
echo "[4/6] Checking .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from .env.example"
    echo
    echo "  >> Edit .env with your Azure AI Foundry endpoint:"
    echo "     AZURE_AI_PROJECT_ENDPOINT=https://..."
    echo "     AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4.1"
    echo
    read -p "  Press Enter when you've configured .env (or Ctrl+C to exit)..."
else
    echo "  .env already exists"
fi

# 5. Pre-flight check
echo "[5/6] Running pre-flight checks..."
uv run python scripts/preflight.py || true

# 6. Validate agents
echo "[6/6] Validating agents..."
uv run python -m agent_core.validate

echo
echo "============================================================"
echo "  Setup complete!"
echo
echo "  Run the platform:"
echo "    uv run --package router-agent python -m router.main"
echo
echo "  Or use the Makefile:"
echo "    make run"
echo "============================================================"

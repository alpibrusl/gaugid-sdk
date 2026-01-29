#!/bin/bash
# Setup script for local development with a2p SDK from ../a2p
# Uses uv and venv for dependency management

set -e

cd "$(dirname "$0")"

echo "═══════════════════════════════════════════════════════════"
echo "     🔧 Gaugid SDK Local Development Setup"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Find a2p SDK location
A2P_SDK_PATH=""
if [ -f "../../a2p/packages/sdk/python/pyproject.toml" ]; then
    A2P_SDK_PATH="../../a2p/packages/sdk/python"
    echo "✅ Found a2p SDK at: $A2P_SDK_PATH"
elif [ -d "../../a2p/packages/sdk-python" ] && [ -f "../../a2p/packages/sdk-python/pyproject.toml" ]; then
    A2P_SDK_PATH="../../a2p/packages/sdk-python"
    echo "✅ Found a2p SDK at: $A2P_SDK_PATH"
elif [ -d "../../a2p" ] && [ -f "../../a2p/pyproject.toml" ]; then
    A2P_SDK_PATH="../../a2p"
    echo "✅ Found a2p SDK at: $A2P_SDK_PATH"
else
    echo "⚠️  a2p SDK not found at ../../a2p"
    echo "   Cannot proceed without it"
    A2P_SDK_PATH=""
fi

# Install a2p SDK from local path if found
if [ -n "$A2P_SDK_PATH" ]; then
    echo ""
    echo "📦 Installing local a2p SDK..."
    cd "$A2P_SDK_PATH"
    if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        uv pip install -e . 2>&1 | tail -5
        echo "   ✅ a2p SDK installed from local path"
    else
        echo "   ⚠️  No pyproject.toml or setup.py found in $A2P_SDK_PATH"
        echo "   ❌ Cannot proceed without a2p SDK"
        exit 1
    fi
    cd - > /dev/null
else
    echo ""
    echo "   ❌ a2p SDK not found. Cannot proceed without it."
    echo "   Please ensure ../../a2p exists with the SDK code."
    exit 1
fi

# Install gaugid SDK core dependencies (without a2p-sdk)
echo ""
echo "📦 Installing gaugid SDK core dependencies..."
uv pip install httpx>=0.25.0 pydantic>=2.0.0 cryptography>=41.0.0 2>&1 | tail -5

# Install dev dependencies
echo ""
echo "📦 Installing dev dependencies..."
uv pip install pytest>=8.0.0 pytest-asyncio>=0.23.0 pytest-cov>=4.1.0 pytest-mock>=3.12.0 mypy>=1.8.0 ruff>=0.1.0 black>=24.0.0 pre-commit>=3.6.0 types-requests>=2.31.0 2>&1 | tail -5

# Install gaugid SDK in editable mode (without dependency resolution)
echo ""
echo "📦 Installing gaugid SDK (editable mode, no deps)..."
pip install -e . --no-deps 2>&1 | tail -3

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "                    ✨ Setup Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "💡 You can now:"
echo "   - Run tests: pytest"
echo "   - Run coverage: pytest --cov=gaugid"
echo "   - Run linting: make lint"
echo "   - Run type checking: make type-check"
echo ""
if [ -n "$A2P_SDK_PATH" ]; then
    echo "✅ Using local a2p SDK from: $A2P_SDK_PATH"
else
    echo "⚠️  Using published a2p-sdk package"
fi
echo ""

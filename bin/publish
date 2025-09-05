#!/bin/bash
# Build and publish package to PyPI

set -e

echo "📦 Building and publishing freyja to PyPI..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package
echo "🔨 Building package..."
poetry build

# Show build info
echo "📋 Build information:"
ls -la dist/

# Configure PyPI authentication if needed
echo "🔐 Configuring PyPI authentication..."
if [ -z "$PYPI_TOKEN" ]; then
    echo "❌ PYPI_TOKEN environment variable not set"
    echo "Please set PYPI_TOKEN environment variable with your PyPI token"
    exit 1
fi

# Configure authentication using http-basic method (more reliable)
poetry config repositories.pypi https://upload.pypi.org/legacy/
poetry config http-basic.pypi __token__ "$PYPI_TOKEN"

# Publish to PyPI
echo "🚀 Publishing to PyPI..."
poetry publish

echo "✅ Published successfully to https://pypi.org/project/freyja/"
echo "📥 Install with: pip install freyja"
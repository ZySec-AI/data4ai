#!/bin/bash

# PyPI Upload Script for data4ai

echo "📦 Data4AI PyPI Upload Script"
echo "=============================="
echo ""

# Check if TWINE_PASSWORD is set
if [ -z "$TWINE_PASSWORD" ]; then
    echo "❌ Error: TWINE_PASSWORD environment variable is not set"
    echo ""
    echo "To upload to PyPI, you need to:"
    echo "1. Create a PyPI account at https://pypi.org/account/register/"
    echo "2. Generate an API token at https://pypi.org/manage/account/token/"
    echo "3. Set the token as an environment variable:"
    echo "   export TWINE_PASSWORD='pypi-YOUR_TOKEN_HERE'"
    echo ""
    echo "For TestPyPI (recommended for first-time uploads):"
    echo "1. Create a TestPyPI account at https://test.pypi.org/account/register/"
    echo "2. Generate an API token at https://test.pypi.org/manage/account/token/"
    echo "3. Set the token and run:"
    echo "   export TWINE_PASSWORD='pypi-YOUR_TEST_TOKEN_HERE'"
    echo "   uv run twine upload --repository testpypi dist/*"
    exit 1
fi

echo "✅ PyPI token found"
echo ""

# Show package info
echo "📋 Package Information:"
echo "-----------------------"
ls -lh dist/
echo ""

# Ask for confirmation
read -p "Upload to PyPI? (y/n for PyPI, t for TestPyPI): " choice

case "$choice" in
    y|Y)
        echo "📤 Uploading to PyPI..."
        uv run twine upload dist/* --username __token__
        echo ""
        echo "✅ Upload complete!"
        echo "View your package at: https://pypi.org/project/data4ai/"
        ;;
    t|T)
        echo "📤 Uploading to TestPyPI..."
        uv run twine upload --repository testpypi dist/* --username __token__
        echo ""
        echo "✅ Upload complete!"
        echo "View your package at: https://test.pypi.org/project/data4ai/"
        echo ""
        echo "To install from TestPyPI:"
        echo "pip install -i https://test.pypi.org/simple/ data4ai"
        ;;
    *)
        echo "❌ Upload cancelled"
        exit 1
        ;;
esac

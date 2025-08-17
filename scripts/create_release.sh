#!/bin/bash

# Create a git tag and push it to trigger the PyPI publish workflow

VERSION="0.1.3"  # Current version in pyproject.toml

echo "📦 Creating release for data4ai v${VERSION}"
echo "========================================="

# Create and push tag
echo "Creating git tag v${VERSION}..."
git tag -a "v${VERSION}" -m "Release v${VERSION}

- Fixed DSPy integration detection
- Improved concurrent batch processing  
- Fixed all linting issues
- Prepared codebase for public release"

echo "Pushing tag to GitHub..."
git push origin "v${VERSION}"

echo ""
echo "✅ Tag created and pushed!"
echo ""
echo "This will trigger the GitHub Actions workflow to:"
echo "1. Run tests"
echo "2. Build the package"
echo "3. Upload to PyPI automatically"
echo ""
echo "Monitor the workflow at:"
echo "https://github.com/data4ai/data4ai/actions"
echo ""
echo "Or create a GitHub release manually at:"
echo "https://github.com/data4ai/data4ai/releases/new"

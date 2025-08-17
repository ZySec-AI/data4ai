# Publishing Data4AI to PyPI

This guide covers the process of building and publishing Data4AI to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts at:
   - [PyPI](https://pypi.org/account/register/)
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)

2. **API Tokens**: Generate API tokens for both PyPI and TestPyPI:
   - Go to Account Settings → API tokens
   - Create a token with "Upload packages" scope
   - Save tokens securely

3. **Install Build Tools**:
   ```bash
   pip install --upgrade build twine
   ```

## Version Management

The version is defined in `pyproject.toml`. The package uses `importlib.metadata` to read the version at runtime.

To update the version:
1. Edit `pyproject.toml` and update the `version` field
2. Update `CHANGELOG.md` with release notes
3. Commit the changes: `git commit -am "Bump version to X.Y.Z"`
4. Tag the release: `git tag vX.Y.Z`

## Build Process

### 1. Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info
```

### 2. Build the Package

```bash
python -m build
```

This creates:
- `dist/data4ai-X.Y.Z-py3-none-any.whl` (wheel distribution)
- `dist/data4ai-X.Y.Z.tar.gz` (source distribution)

### 3. Verify the Build

```bash
# Check package metadata and README rendering
twine check dist/*

# Inspect package contents
tar -tzf dist/data4ai-*.tar.gz | head -20
unzip -l dist/data4ai-*.whl | head -20
```

## Testing

### 1. Test Local Installation

```bash
# Create a clean virtual environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from wheel
pip install dist/data4ai-*.whl

# Test basic functionality
data4ai --version
data4ai --help
python -c "from data4ai import __version__; print(__version__)"

# Test with extras
pip install dist/data4ai-*.whl[excel,hf]

# Cleanup
deactivate
rm -rf test-env
```

### 2. Test on TestPyPI

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install -i https://test.pypi.org/simple/ data4ai

# With extras (may need --extra-index-url for dependencies)
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple data4ai[excel,hf]
```

## Publishing to PyPI

### 1. Final Checks

- [ ] All tests pass
- [ ] Version number is correct
- [ ] CHANGELOG.md is updated
- [ ] README renders correctly on TestPyPI
- [ ] Installation from TestPyPI works

### 2. Upload to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: <your-pypi-api-token>
```

### 3. Verify Publication

```bash
# Wait a few minutes for PyPI to update, then:
pip install data4ai

# Verify the installation
data4ai --version
```

### 4. Create GitHub Release

1. Go to GitHub repository → Releases → Draft a new release
2. Choose tag: `vX.Y.Z`
3. Release title: `Data4AI vX.Y.Z`
4. Copy release notes from CHANGELOG.md
5. Attach the wheel and source distribution files
6. Publish release

## Using .pypirc (Optional)

For convenience, create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-token-here

[testpypi]
username = __token__
password = pypi-your-test-token-here
```

Then you can upload without entering credentials:
```bash
twine upload --repository pypi dist/*
twine upload --repository testpypi dist/*
```

## Automated Publishing (GitHub Actions)

See `.github/workflows/publish.yml` for automated publishing on tagged releases.

To use:
1. Add PyPI API token as GitHub secret: `PYPI_API_TOKEN`
2. Push a tag: `git push origin vX.Y.Z`
3. GitHub Actions will automatically build and publish

## Troubleshooting

### "Invalid distribution file"
- Ensure you're using the latest versions of build and twine
- Check that the version in pyproject.toml is valid (PEP 440)

### "The description failed to render"
- Run `twine check dist/*` to identify issues
- Ensure README.md is valid Markdown
- Check for broken links or invalid syntax

### "Version already exists"
- You cannot overwrite existing versions on PyPI
- Increment the version number and rebuild

### Installation Issues
- Verify all dependencies are available on PyPI
- Check that optional dependencies are properly specified
- Test with `--no-deps` flag to isolate dependency issues

## Security Notes

- Never commit API tokens to version control
- Use GitHub Secrets for CI/CD tokens
- Rotate tokens periodically
- Use 2FA on PyPI account

## Release Checklist

Before each release:

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md`
- [ ] Run full test suite
- [ ] Test build: `python -m build`
- [ ] Check package: `twine check dist/*`
- [ ] Test on TestPyPI
- [ ] Create git tag
- [ ] Publish to PyPI
- [ ] Create GitHub Release
- [ ] Announce release (if applicable)
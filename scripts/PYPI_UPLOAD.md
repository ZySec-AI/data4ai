# PyPI Upload Instructions for data4ai

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/account/register/
2. **API Token**: Generate a token at https://pypi.org/manage/account/token/
3. **Test First**: Consider using TestPyPI first: https://test.pypi.org/

## Upload Steps

### 1. Set your PyPI token

```bash
export TWINE_PASSWORD="pypi-YOUR_TOKEN_HERE"
```

### 2. Verify the build

```bash
# Check packages are valid
uv run twine check dist/*

# Should show:
# Checking dist/data4ai-0.1.1-py3-none-any.whl: PASSED
# Checking dist/data4ai-0.1.1.tar.gz: PASSED
```

### 3. Upload to PyPI

#### Option A: Use the upload script (Recommended)
```bash
./upload_to_pypi.sh
```

#### Option B: Direct upload
```bash
# For production PyPI
uv run twine upload dist/* --username __token__

# For TestPyPI (recommended for first upload)
uv run twine upload --repository testpypi dist/* --username __token__
```

### 4. Verify the upload

- Production: https://pypi.org/project/data4ai/
- TestPyPI: https://test.pypi.org/project/data4ai/

### 5. Test installation

```bash
# From production PyPI
pip install data4ai

# From TestPyPI
pip install -i https://test.pypi.org/simple/ data4ai
```

## Version Management

Before uploading a new version:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Rebuild: `rm -rf dist/ && uv run python -m build`
4. Upload new version

## Common Issues

- **409 Conflict**: Version already exists. Bump version in pyproject.toml
- **401 Unauthorized**: Check your TWINE_PASSWORD token
- **400 Bad Request**: Run `uv run twine check dist/*` to validate packages

## Current Package Info

- **Name**: data4ai
- **Version**: 0.1.1
- **License**: MIT
- **Python**: >=3.9
- **Homepage**: https://github.com/zysec/data4ai
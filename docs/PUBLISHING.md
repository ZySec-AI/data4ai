# 📦 Publishing to PyPI

This document explains how to publish the `data4ai` package to PyPI using the GitHub Actions workflows.

## 🚀 Publishing Workflows

We have two workflows for publishing to PyPI:

### 1. **Automatic Publishing** (`publish.yml`)
- **Triggers**: 
  - When a GitHub release is published
  - When a tag starting with `v` is pushed (e.g., `v0.1.2`)
  - Manual workflow dispatch with TestPyPI option
- **Targets**: PyPI (production) or TestPyPI (testing)
- **Safety**: Includes comprehensive testing and validation

### 2. **Manual Publishing** (`manual-publish.yml`)
- **Triggers**: Manual workflow dispatch only
- **Features**: More control options, version validation, force publishing
- **Use cases**: Hotfixes, beta releases, testing

## 📋 Prerequisites

### Required Secrets
Make sure this secret is configured in your GitHub repository:

1. **`PYPI_API_TOKEN`** - Your PyPI API token

### Getting API Tokens

#### PyPI Token
1. Go to [PyPI](https://pypi.org)
2. Log in to your account
3. Go to Account Settings → API tokens
4. Create a new token with "Entire account" scope
5. Copy the token and add it to GitHub secrets



## 🔄 Publishing Process

### Step 1: Update Version
Before publishing, update the version in `pyproject.toml`:

```toml
[project]
version = "0.1.2"  # Update this
```

### Step 2: Choose Publishing Method

#### Method A: Automatic Publishing (Recommended)

1. **Create a tag**:
   ```bash
   git tag v0.1.2
   git push origin v0.1.2
   ```

2. **Or create a GitHub release**:
   - Go to GitHub → Releases → Create a new release
   - Tag version: `v0.1.2`
   - Title: `Release v0.1.2`
   - Publish the release

#### Method B: Manual Publishing

1. Go to GitHub → Actions → Manual PyPI Publish
2. Click "Run workflow"
3. Configure options:
   - **Version**: Leave empty to use current version, or specify a version
   - **Force**: Check if you want to overwrite existing version
   - **Skip tests**: Only check if you're confident in the code

### Step 3: Monitor the Workflow

The workflow will:

1. **Validate** the code (linting, tests)
2. **Build** the package
3. **Test** installation across Python versions
4. **Publish** to the target repository
5. **Verify** the upload
6. **Create** GitHub release (if applicable)

## 🧪 Testing Before Production

### Local Testing
Test locally before publishing to PyPI:

1. Build and test the package locally
2. Verify all functionality works as expected
3. Run the full test suite

```bash
# Build package
python -m build

# Check package
twine check dist/*

# Test installation
pip install dist/*.whl

# Test functionality
data4ai version
data4ai --help
```

## 📦 Package Variants

The package supports different installation variants:

```bash
# Basic installation
pip install data4ai

# With Excel support
pip install data4ai[excel]

# With HuggingFace support
pip install data4ai[hf]

# With all features
pip install data4ai[all]
```

## 🔍 Workflow Features

### Automatic Publishing Workflow
- ✅ **Version consistency check** - Ensures tag version matches package version
- ✅ **Comprehensive testing** - Runs tests across Python 3.9-3.12
- ✅ **Package validation** - Validates package metadata and structure
- ✅ **Installation testing** - Tests all package variants
- ✅ **Automatic release creation** - Creates GitHub releases with assets

### Manual Publishing Workflow
- ✅ **Input validation** - Validates workflow inputs
- ✅ **Version checking** - Warns about version mismatches
- ✅ **Flexible targets** - Choose between TestPyPI and PyPI
- ✅ **Force publishing** - Override existing versions if needed
- ✅ **Skip tests option** - Bypass testing for urgent fixes
- ✅ **Detailed logging** - Comprehensive output for debugging

## 🚨 Safety Features

### Version Protection
- Prevents publishing if version doesn't match tag
- Warns about version mismatches
- Validates package metadata

### Testing Requirements
- Runs linting (ruff, black)
- Executes all tests with coverage
- Tests installation across Python versions
- Validates package structure

### Rollback Protection
- Uses `skip-existing: true` to prevent accidental overwrites
- Force option available for intentional overwrites
- Comprehensive logging for troubleshooting

## 📊 Monitoring

### Workflow Status
Monitor workflow execution in GitHub Actions:
- Green checkmark = Success
- Red X = Failure (check logs for details)
- Yellow warning = Partial success

### Package Verification
After publishing, verify:
1. Package appears on PyPI/TestPyPI
2. Installation works: `pip install data4ai`
3. CLI works: `data4ai --version`
4. All features work as expected

## 🐛 Troubleshooting

### Common Issues

#### "Package validation failed"
- Check `pyproject.toml` syntax
- Ensure all required fields are present
- Verify package structure

#### "Version mismatch"
- Update version in `pyproject.toml`
- Ensure tag version matches package version
- Commit and push changes

#### "Authentication failed"
- Check API tokens in GitHub secrets
- Verify token permissions
- Ensure tokens are valid and not expired

#### "Package already exists"
- Use force option to overwrite
- Or increment version number
- Check if version was already published

### Getting Help
- Check workflow logs for detailed error messages
- Review this documentation
- Open an issue on GitHub if problems persist

## 📈 Best Practices

1. **Always test locally before publishing**
2. **Use semantic versioning** (e.g., 0.1.2, 1.0.0)
3. **Update CHANGELOG.md** before releasing
4. **Test installation** after publishing
5. **Monitor package downloads** and user feedback
6. **Keep dependencies updated** and secure

## 🔗 Useful Links

- [PyPI](https://pypi.org/project/data4ai/)
- [GitHub Actions](https://github.com/zysec/data4ai/actions)
- [Package Documentation](https://github.com/zysec/data4ai#readme)
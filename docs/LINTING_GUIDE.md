# Linting Guide

This guide covers the comprehensive linting setup for the media uploader project, including code formatting, style checking, type checking, and security analysis.

## Overview

The project uses multiple linting tools to ensure code quality:

- **Black**: Code formatter for consistent Python formatting
- **isort**: Import sorter for organized imports
- **Flake8**: Style guide enforcement and error detection
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability detection
- **Pre-commit**: Automated hooks for consistent code quality

## Quick Start

### Installation

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

### Running Linters

Use the convenient linting script:

```bash
# Run all linters
python run_lint.py --all

# Check formatting without changes
python run_lint.py --all --check

# Run specific linter
python run_lint.py --black
python run_lint.py --flake8
python run_lint.py --mypy

# Lint specific files
python run_lint.py --files app/ui/main_window.py core/auth_manager.py
```

### Pre-commit Setup

Install pre-commit hooks for automatic linting on commit:

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

## Tool Configuration

### Black (Code Formatter)

**Configuration**: `pyproject.toml` → `[tool.black]`

- **Line length**: 88 characters (compatible with flake8)
- **Target version**: Python 3.8+
- **Excludes**: `private/`, `demo_media/`, build artifacts

**Usage**:
```bash
# Format code
black .

# Check formatting
black --check .

# Format specific files
black app/ui/main_window.py
```

### isort (Import Sorter)

**Configuration**: `pyproject.toml` → `[tool.isort]`

- **Profile**: Black-compatible
- **Line length**: 88 characters
- **Known sections**: First-party modules (`app`, `core`, `services`, `infra`)
- **Skip**: `private/`, `demo_media/`, build artifacts

**Usage**:
```bash
# Sort imports
isort .

# Check import sorting
isort --check-only .

# Sort specific files
isort app/ui/main_window.py
```

### Flake8 (Style Guide)

**Configuration**: `.flake8`

- **Line length**: 88 characters
- **Excludes**: `private/`, `demo_media/`, build artifacts
- **Ignored codes**: 
  - `E203`, `E231`, `W503`, `W504`: Handled by Black
  - `E402`: Module-level imports not at top (conditional imports)
  - `E731`: Lambda expressions (sometimes clearer than def)
  - `F811`: Redefined names (test fixtures)
  - `F401`, `F841`: Unused imports/variables (__init__.py files)

**Usage**:
```bash
# Run flake8
flake8 .

# Run with specific files
flake8 app/ core/
```

### MyPy (Type Checker)

**Configuration**: `pyproject.toml` → `[tool.mypy]`

- **Python version**: 3.8
- **Strict settings**: Enabled for most checks
- **Module overrides**: Ignore missing imports for third-party libraries
- **Per-module options**: Relaxed typing for UI and test files

**Usage**:
```bash
# Type check all modules
mypy app core services infra

# Type check specific module
mypy app/ui/main_window.py

# Show error codes
mypy --show-error-codes app/
```

### Bandit (Security)

**Configuration**: `pyproject.toml` → `[tool.bandit]`

- **Output format**: JSON report
- **Excludes**: `tests/`, `private/`, `demo_media/`
- **Report file**: `bandit-report.json`

**Usage**:
```bash
# Security scan
bandit -r . -f json -o bandit-report.json

# Scan specific files
bandit app/ui/main_window.py
```

## Pre-commit Hooks

**Configuration**: `.pre-commit-config.yaml`

The pre-commit configuration includes:

1. **Basic hooks**: Trailing whitespace, file endings, YAML validation
2. **Formatting**: Black and isort
3. **Linting**: Flake8 and MyPy
4. **Security**: Bandit
5. **Testing**: Pytest (manual stage)

**Hook stages**:
- **Pre-commit**: Automatic formatting and basic checks
- **Manual**: Testing (run with `pre-commit run pytest-check --all-files`)

## Integration with IDE

### VS Code

Add to `.vscode/settings.json`:

```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.banditEnabled": true,
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### PyCharm

1. **Black**: Install Black plugin and configure as external tool
2. **isort**: Configure as external tool
3. **Flake8**: Enable in Settings → Tools → External Tools
4. **MyPy**: Enable in Settings → Tools → External Tools

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Lint and Test

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      - name: Run linting
        run: |
          python run_lint.py --all --check
      
      - name: Run tests
        run: |
          python run_tests.py --type unit
```

## Common Issues and Solutions

### Black vs Flake8 Conflicts

**Issue**: Black and Flake8 have different opinions about formatting.

**Solution**: The `.flake8` configuration ignores codes that Black handles:
- `E203`: Whitespace before ':'
- `E231`: Missing whitespace after ','
- `W503`, `W504`: Line break before/after binary operator

### MyPy Import Errors

**Issue**: MyPy can't find third-party library type stubs.

**Solution**: The `pyproject.toml` configuration includes:
```toml
[[tool.mypy.overrides]]
module = ["PySide6.*", "google.*", "pytest.*"]
ignore_missing_imports = true
```

### Pre-commit Hook Failures

**Issue**: Pre-commit hooks fail on existing code.

**Solution**: 
1. Run formatters first: `black . && isort .`
2. Fix linting issues: `flake8 .`
3. Install hooks: `pre-commit install`

### Type Annotation Issues

**Issue**: MyPy complains about missing type annotations.

**Solution**: 
1. Add type hints gradually
2. Use `# type: ignore` comments for problematic lines
3. Configure per-module options in `pyproject.toml`

## Best Practices

### Code Organization

1. **Imports**: Use isort to maintain consistent import order
2. **Formatting**: Let Black handle all formatting decisions
3. **Type hints**: Add type annotations for function parameters and return values
4. **Documentation**: Use docstrings for public functions and classes

### Workflow

1. **Before committing**: Run `python run_lint.py --all --check`
2. **Fix issues**: Address any linting errors
3. **Format code**: Run `python run_lint.py --black --isort`
4. **Commit**: Use pre-commit hooks for automatic checks

### Configuration Management

1. **Don't modify tool configs** unless necessary
2. **Use per-file ignores** for specific cases
3. **Keep configurations in sync** across tools
4. **Document custom configurations** in this guide

## Troubleshooting

### Installation Issues

```bash
# Clean install
pip uninstall -r requirements-dev.txt
pip install -r requirements-dev.txt

# Virtual environment issues
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Performance Issues

```bash
# Run specific tools only
python run_lint.py --flake8 app/

# Use parallel processing (where supported)
pytest -n auto  # For tests
```

### Configuration Issues

1. **Check file locations**: Ensure config files are in project root
2. **Verify syntax**: Check YAML/TOML syntax
3. **Clear caches**: Remove `.mypy_cache/`, `__pycache__/`
4. **Update tools**: `pip install --upgrade -r requirements-dev.txt`

## Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)

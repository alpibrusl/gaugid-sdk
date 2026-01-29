# Development Guide

This document outlines the development setup, testing, and code quality standards for the Gaugid SDK.

## Quick Start

### Standard Setup (Published a2p-sdk)

```bash
# Install with dev dependencies
make install-dev

# Run all checks
make ci

# Run tests with coverage
make test-cov
```

### Local Development Setup (Local a2p SDK)

If you have the a2p SDK code in `../../a2p`, you can use it for local development:

```bash
# Using the setup script (recommended)
bash setup-local-dev.sh

# Or using Makefile
make install-dev-local

# Or step by step:
# 1. Install local a2p SDK
cd ../../a2p/packages/sdk/python  # pyproject.toml is here
pip install -e .

# 2. Install gaugid SDK
cd ../../gaugid-sdk/gaugid-sdk-python
pip install -e ".[dev]"
pre-commit install
```

**Note**: The local a2p SDK path is automatically detected. The setup script looks for:
- `../../a2p/packages/sdk/python/pyproject.toml` (primary path - pyproject.toml is directly in python/)
- `../../a2p/packages/sdk-python/pyproject.toml` (alternative path)
- `../../a2p/pyproject.toml` (if a2p SDK is at root)

## Pre-commit Hooks

We use [pre-commit](https://pre-commit.com/) to ensure code quality before commits.

### Setup

```bash
pre-commit install
```

### What Runs

**On every commit:**
- ✅ Trailing whitespace removal
- ✅ End of file fixes
- ✅ YAML/JSON/TOML validation
- ✅ Merge conflict detection
- ✅ Debug statement detection
- ✅ Code formatting (Black, Ruff format)
- ✅ Linting (Ruff)
- ✅ Type checking (mypy)
- ✅ Security scanning (Bandit)

**On pre-push:**
- ✅ Test coverage check (80% minimum)

### Manual Run

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

## Test Coverage

### Requirements

- **Minimum**: 80% code coverage (enforced)
- **Target**: 90% code coverage
- Coverage is checked in:
  - Pre-commit hooks (pre-push)
  - CI/CD pipeline
  - Local development

### Running Coverage

```bash
# Run tests with coverage
pytest --cov=gaugid --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Or use Makefile
make test-cov
make coverage-report  # Opens HTML report in browser
```

### Coverage Reports

- **HTML Report**: `htmlcov/index.html`
- **Terminal Report**: Shows missing lines
- **JSON Report**: `coverage.json` (for CI)
- **XML Report**: `coverage.xml` (for CI)

### Exclusions

The following are excluded from coverage:
- `__repr__` methods
- `TYPE_CHECKING` blocks
- `@abstractmethod` decorators
- `if __name__ == "__main__"` blocks
- Test files
- Example files

## Code Quality Tools

### Ruff (Linting & Formatting)

Fast Python linter and formatter.

```bash
# Check
ruff check src/ tests/

# Fix
ruff check --fix src/ tests/

# Format
ruff format src/ tests/
```

### Black (Formatting)

Code formatter (used alongside Ruff).

```bash
# Check
black --check src/ tests/

# Format
black src/ tests/
```

### mypy (Type Checking)

Static type checker.

```bash
# Check types
mypy src/gaugid

# Excludes tests and examples
```

### Bandit (Security)

Security linter for Python.

```bash
# Run security scan
bandit -r src/ -ll -f json -o bandit-report.json
```

## CI/CD Pipeline

GitHub Actions runs on every push and PR:

1. **Lint Job**: Ruff, Black, mypy
2. **Test Job**: Tests on Python 3.10, 3.11, 3.12
3. **Coverage Job**: Coverage report generation
4. **Security Job**: Bandit security scan

See `.github/workflows/ci.yml` for details.

## Makefile Commands

```bash
make help          # Show all commands
make install       # Install package
make install-dev   # Install with dev dependencies
make test          # Run tests
make test-cov      # Run tests with coverage
make coverage-report  # Generate and open coverage report
make lint          # Run linters
make format        # Format code
make type-check    # Run type checker
make security      # Run security scan
make pre-commit    # Run all pre-commit hooks
make ci            # Run all CI checks locally
make clean         # Clean build artifacts
```

## Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and test**
   ```bash
   make test-cov
   ```

3. **Format and lint**
   ```bash
   make format
   make lint
   ```

4. **Run pre-commit hooks**
   ```bash
   make pre-commit
   ```

5. **Push (coverage check runs automatically)**
   ```bash
   git push
   ```

## Coverage Goals by Module

| Module | Current | Target | Status |
|--------|---------|--------|--------|
| `client.py` | ~80% | 85% | ✅ |
| `auth.py` | ~85% | 90% | ✅ |
| `storage.py` | ~70% | 85% | ⚠️ |
| `types.py` | ~70% | 80% | ✅ |
| `connection.py` | ~85% | 90% | ✅ |
| `signature.py` | ~85% | 90% | ✅ |
| `utils.py` | ~90% | 90% | ✅ |
| **Overall** | **~80%** | **90%** | ✅ |

## Troubleshooting

### Pre-commit hooks not running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Coverage below 80%

1. Check coverage report: `make coverage-report`
2. Identify missing lines
3. Add tests for uncovered code
4. Re-run: `make test-cov`

### Type checking errors

```bash
# Check specific file
mypy src/gaugid/client.py

# Add type ignores if needed (with justification)
# type: ignore[error-code]  # Reason
```

## Best Practices

1. **Always run tests before committing**
   ```bash
   make test-cov
   ```

2. **Keep coverage above 80%**
   - Add tests for new code
   - Fix failing tests before merging

3. **Follow type hints**
   - Use type annotations
   - Fix mypy errors

4. **Format code before committing**
   ```bash
   make format
   ```

5. **Run security scan**
   ```bash
   make security
   ```

## Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Pytest Coverage](https://pytest-cov.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)

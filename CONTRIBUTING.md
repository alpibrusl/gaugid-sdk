# Contributing to Gaugid SDK

Thank you for your interest in contributing to Gaugid SDK. This document explains how to report issues, propose changes, and set up a development environment.

## Code of conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Internal content

**Do not commit** internal-only docs, secrets, or paths that reference internal repos. See [docs/INTERNAL_CONTENT_POLICY.md](docs/INTERNAL_CONTENT_POLICY.md) for what is considered internal and how to fix accidental commits. CI will fail if tracked files contain internal paths.

## How to contribute

- **Report bugs** — Use [GitHub Issues](https://github.com/alpibrusl/gaugid-sdk/issues) and choose the Bug report template.
- **Suggest features** — Open an issue with the Feature request template.
- **Submit code** — Open a pull request (see below).
- **Improve docs** — PRs to `docs/` and READMEs are welcome.

## Development setup

### Python SDK (`gaugid-sdk-python/`)

1. **Clone and enter the Python package:**
   ```bash
   git clone https://github.com/alpibrusl/gaugid-sdk.git
   cd gaugid-sdk/gaugid-sdk-python
   ```

2. **Create a virtual environment and install:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Run tests:**
   ```bash
   pytest -v
   ```

4. **Lint and format:**
   ```bash
   ruff check src/ tests/
   ruff format src/ tests/
   black src/ tests/
   mypy src/gaugid
   ```

See [gaugid-sdk-python/DEVELOPMENT.md](gaugid-sdk-python/DEVELOPMENT.md) for more detail (local a2p SDK, coverage, etc.).

### TypeScript SDK (`gaugid-sdk-typescript/`)

1. Enter the package and install:
   ```bash
   cd gaugid-sdk/gaugid-sdk-typescript
   npm install
   ```

2. Build and test:
   ```bash
   npm run build
   npm test
   ```

## Pull request process

1. **Fork** the repo and create a branch from `main` (e.g. `fix/issue-123` or `feat/add-xyz`).
2. **Make your changes** and add/update tests where relevant.
3. **Ensure CI passes:** run lint and tests locally (see above).
4. **Open a PR** against `main`. Use the PR template and reference any related issues.
5. **Address review feedback.** Maintainers may request changes.
6. Once approved, a maintainer will merge.

## Code style

- **Python:** Ruff and Black; follow type hints and docstrings. See `gaugid-sdk-python/pyproject.toml` for config.
- **TypeScript:** ESLint and Prettier; follow the existing style in the repo.
- **Docs:** Markdown in `docs/`; keep examples accurate and concise.

## Commit messages

Use clear, present-tense messages:

- `fix: handle empty scope list in OAuth URL`
- `feat: add support for X`
- `docs: update quick start example`
- `test: add tests for propose_memory`

## Questions?

- Open a [Discussion](https://github.com/alpibrusl/gaugid-sdk/discussions) for questions and ideas.
- For security issues, see [SECURITY.md](SECURITY.md).

Thank you for contributing.

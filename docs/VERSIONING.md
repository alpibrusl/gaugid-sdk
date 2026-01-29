# Versioning and release

This document describes how Gaugid SDK is versioned and how to cut a release.

## Version scheme

We use **Semantic Versioning (Semver)** [2.0.0](https://semver.org/spec/v2.0.0.html):

- **MAJOR** — Incompatible API or behavior changes
- **MINOR** — New features, backward compatible
- **PATCH** — Bug fixes and small changes, backward compatible

Pre-release versions use a hyphen: e.g. `0.1.0-alpha`, `1.0.0-rc.1`.

## Where version lives

| Package              | File                    | Variable / key |
|----------------------|-------------------------|----------------|
| Python SDK           | `gaugid-sdk-python/pyproject.toml` | `[project] version = "x.y.z"` |
| TypeScript SDK       | `gaugid-sdk-typescript/package.json` | `"version": "x.y.z"` |

Each package has its **own version**. They do not need to stay in sync; bump when you release that package.

## Changelog

- **Root**: [CHANGELOG.md](../CHANGELOG.md) — High-level project history and notable changes for the whole repo.
- **Per-package**: Optional. Python and TypeScript can document changes in the root CHANGELOG under a `[Package]` section, or in package-specific docs.

When you cut a release, add an entry under a new version heading (e.g. `## [0.1.1] - YYYY-MM-DD`) with Added / Changed / Fixed / Removed.

## Steps to release

### 1. Decide version and scope

- **Patch** (e.g. 0.1.0 → 0.1.1): Bug fixes, docs, no API change.
- **Minor** (e.g. 0.1.0 → 0.2.0): New features, backward compatible.
- **Major** (e.g. 0.1.0 → 1.0.0): Breaking changes.

### 2. Update version in source

- **Python**: Edit `gaugid-sdk-python/pyproject.toml` → `version = "x.y.z"`.
- **TypeScript**: Edit `gaugid-sdk-typescript/package.json` → `"version": "x.y.z"`.

### 3. Update CHANGELOG

- Add a new section `## [x.y.z] - YYYY-MM-DD` in [CHANGELOG.md](../CHANGELOG.md).
- List changes (Added, Changed, Fixed, Removed).
- Update the “Unreleased” link at the bottom to point to the new tag.

### 4. Commit and tag

```bash
git add gaugid-sdk-python/pyproject.toml gaugid-sdk-typescript/package.json CHANGELOG.md
git commit -m "chore: release v0.1.1"
git tag -a v0.1.1 -m "Release v0.1.1"
git push origin main
git push origin v0.1.1
```

For **package-specific** releases you can use tags like `gaugid-python/v0.1.1` and `gaugid-ts/v0.1.1`, and document that convention in this file.

### 5. Publish packages

- **Python (PyPI)**  
  From repo root:
  ```bash
  cd gaugid-sdk-python
  python -m build
  twine upload dist/*
  ```
  Use a PyPI token; do not commit credentials.

- **TypeScript (npm)**  
  From repo root:
  ```bash
  cd gaugid-sdk-typescript
  npm publish --access public
  ```
  Use `npm login` or CI secrets; do not commit tokens.

### 6. GitHub Release (optional)

- Open **Releases** → **Draft a new release**.
- Choose the tag (e.g. `v0.1.1`).
- Title: `Release v0.1.1`.
- Description: Copy the relevant part of CHANGELOG for this version.
- Attach any artifacts (e.g. `dist/*.whl`, `dist/*.tar.gz`) if you want them on GitHub.

## Checklist before release

- [ ] Version bumped in the package(s) you are releasing.
- [ ] CHANGELOG updated with the new version and date.
- [ ] Tests and CI pass.
- [ ] No internal-only paths or secrets in the repo (see [INTERNAL_CONTENT_POLICY.md](INTERNAL_CONTENT_POLICY.md)).
- [ ] Tag created and pushed.
- [ ] Package published to PyPI / npm as needed.
- [ ] GitHub Release created (optional).

## Automation (future)

You can add a GitHub Actions workflow that:

- Runs on tag push (e.g. `v*`).
- Builds and publishes to PyPI and/or npm using repository secrets.
- Creates or updates a GitHub Release from CHANGELOG.

Until then, use the manual steps above.

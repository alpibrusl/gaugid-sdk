# Open source release checklist

Use this as a quick reference for a professional, “rock star” open source repo.

## ✅ What’s in place

| Item | Location |
|------|----------|
| **Root README** | [README.md](../README.md) — badges, quick start, structure, links |
| **License** | [LICENSE](../LICENSE) — EUPL-1.2 (root and Python/TS packages) |
| **Contributing** | [CONTRIBUTING.md](../CONTRIBUTING.md) — how to contribute, dev setup, PR process |
| **Code of conduct** | [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) — Contributor Covenant 2.1 |
| **Security** | [SECURITY.md](../SECURITY.md) — how to report vulnerabilities |
| **Changelog** | [CHANGELOG.md](../CHANGELOG.md) — version history |
| **Issue templates** | [.github/ISSUE_TEMPLATE/](../.github/ISSUE_TEMPLATE/) — bug, feature, config |
| **PR template** | [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md) |
| **CI** | [.github/workflows/ci.yml](../.github/workflows/ci.yml) — lint, test, security (Python) |
| **Dependabot** | [.github/dependabot.yml](../.github/dependabot.yml) — monthly dependency updates |
| **Root .gitignore** | [.gitignore](../.gitignore) — common artifacts, subdirs |

## Internal content and versioning

- **Internal content**: [INTERNAL_CONTENT_POLICY.md](INTERNAL_CONTENT_POLICY.md) — what must not be committed; CI fails if internal paths are tracked.
- **Versioning**: [VERSIONING.md](VERSIONING.md) — semver, where version lives, and release steps.

## Optional next steps

- **GitHub Discussions** — Enable in repo Settings → General → Features.
- **Codecov / coverage badge** — After first CI run, add a coverage badge to the root README (Codecov provides the URL).
- **PyPI publish** — When ready: `cd gaugid-sdk-python && python -m build && twine upload dist/*` (use PyPI token).
- **npm publish** — When TypeScript SDK is ready: `cd gaugid-sdk-typescript && npm publish --access public`.
- **Release workflow** — Add a `.github/workflows/release.yml` for tagging and publishing (e.g. PyPI + GitHub Release).
- **Stale issues** — Optional [stale](https://github.com/actions/stale) workflow to close inactive issues/PRs.
- **Labels** — Add labels: `bug`, `enhancement`, `documentation`, `good first issue`, `help wanted`, `dependencies`, `python`, `typescript`.

## Badges (root README)

Current badges point to:

- **CI** — `https://github.com/alpibrusl/gaugid-sdk/actions/workflows/ci.yml`
- **License** — EUPL-1.2
- **Python** — 3.10+
- **Ruff** — code style

After enabling Codecov, add:

```markdown
[![codecov](https://codecov.io/gh/alpibrusl/gaugid-sdk/graph/badge.svg)](https://codecov.io/gh/alpibrusl/gaugid-sdk)
```

## First-time repo setup on GitHub

1. Create repo (e.g. `alpibrusl/gaugid-sdk`), then push.
2. **Settings → General:** Add description, website (e.g. docs.gaugid.com), topics (`gaugid`, `a2p`, `sdk`, `python`, `typescript`, `oauth`, `ai-agents`).
3. **Settings → General → Features:** Enable Issues, Discussions (optional), Wiki (optional).
4. **Settings → Branches:** Add branch protection for `main` (require PR reviews, status checks: CI).
5. **Settings → Secrets:** Add `CODECOV_TOKEN` if using Codecov; add PyPI/npm tokens when automating releases.

Done. You’re ready for a professional open source release.

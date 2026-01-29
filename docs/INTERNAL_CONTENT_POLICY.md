# Internal content policy

This document describes what **must not** appear in the public Gaugid SDK repository and how to keep the repo safe for open source.

## What is internal

- **`.internal-docs/`** — Internal design notes, compliance reviews, release plans, and strategy. Never commit this directory.
- **References to other internal paths** — Do not link to `a2p-cloud/.internal-docs/`, `../.internal-docs/`, or similar in **public** docs (e.g. `docs/`, `README`, examples). Use generic wording or public URLs instead.
- **Secrets and credentials** — API keys, tokens, `.env` with real values, `tokens.json` with real tokens. Use `.gitignore` and env vars.
- **Proprietary or confidential text** — Internal roadmap, unreleased product details, or confidential partner info. Keep in internal tools only.

## .gitignore

The root [.gitignore](../.gitignore) already excludes:

- `.internal-docs/`
- `.env`, `.env.local`
- Build artifacts, venvs, IDE files

If you add new internal paths (e.g. `internal/`, `*.internal.md`), add them to `.gitignore` and to this policy.

## If internal content was committed

1. **Do not** push more commits that reference it. Fix the content first.
2. **Remove** the file from the index but keep it on disk (so it stays only in your clone):
   ```bash
   git rm -r --cached .internal-docs/
   git commit -m "chore: stop tracking .internal-docs (internal content policy)"
   ```
3. **Rewrite history** if the content was pushed and must be removed from history (e.g. `git filter-branch` or BFG). Prefer contacting a maintainer; they can use GitHub’s guidance for removing sensitive data.
4. **Rotate** any exposed secrets immediately.

## Public docs

- In `docs/`, `README`, and examples, **do not** link to `.internal-docs/` or to other repos’ internal paths.
- Use neutral wording instead, e.g. “See the a2p protocol specification” or “Implementation details are documented in the integration guide.”

## Before first public push

If `.internal-docs/` (or any internal path) was ever committed, remove it from tracking **before** pushing the repo public:

```bash
# From repo root
git rm -r --cached .internal-docs/   # if it exists and was tracked
git commit -m "chore: stop tracking .internal-docs (internal content policy)"
```

Then push. The directory stays on disk but is no longer in the repo. Ensure `.internal-docs/` is in `.gitignore` (it is).

## CI

The repository CI includes a check that **no tracked file** lives under `.internal-docs/` or is named in a way that suggests internal-only content. If that check fails, remove or move the content and update `.gitignore` as above.

# NoteStore Lab Claude Code Plugin

This directory is a Claude Code plugin and a Git-backed marketplace-ready
artifact.

It bundles:

- a plugin manifest
- a plugin-root `.mcp.json`
- a launcher that keeps the server pinned to one explicit case root

## Required Environment

Set these before you enable the plugin:

- `NOTESTORELAB_REPO_ROOT`
- `NOTESTORELAB_CASE_DIR`
- optional: `NOTESTORELAB_PYTHON`

The bundled launcher uses `NOTESTORELAB_PYTHON` when present. Otherwise it
falls back to `$NOTESTORELAB_REPO_ROOT/.venv/bin/python`.

## Public Distribution Surface

The repository root ships `.claude-plugin/marketplace.json`, so the repository
itself can be added as a Claude Code marketplace.

Example:

```bash
claude plugin marketplace add xiaojiou176/apple-notes-forensics
claude plugin install notestorelab-claude-plugin@notestorelab-plugins
```

This plugin directory is also the source used for the OpenClaw-compatible
bundle archive built by `scripts/release/build_distribution_bundles.py`.

# Distribution Surface

This file is the exact claim boundary for NoteStore Lab's public distribution
story.

Use it when you need to answer:

- what counts as official
- what counts as public-ready only
- what is already listed
- what still requires manual external action

## Public Distribution Matrix

| Surface | Official public surface exists | Repo-owned artifact shipped | Already listed | Current truthful claim |
| --- | --- | --- | --- | --- |
| MCP Registry | yes, the official MCP Registry exists and is still documented as a preview surface | yes: `server.json` and `notes-recovery-mcp` | not confirmed | registry metadata draft shipped and points at a live PyPI package; do not claim canonical alignment, submission success, or listing without fresh registry read-back |
| Codex | yes, the official Codex plugin directory exists, but third-party official-directory submission is still coming soon | yes: `plugins/notestorelab-codex-plugin/` | not confirmed | public-ready Codex plugin bundle shipped; do not claim official Codex directory listing |
| Claude Code | yes, official plugin and marketplace surfaces exist | yes: `plugins/notestorelab-claude-plugin/` plus root `.claude-plugin/marketplace.json` | not confirmed | submit-ready Claude Code marketplace artifact shipped; do not claim Anthropic-managed listing without fresh read-back |
| OpenClaw | yes, the official ClawHub public registry exists | yes: `plugins/notestorelab-openclaw-bundle/` | not confirmed | public-ready compatible bundle shipped; do not claim live ClawHub or official OpenClaw listing |

## Repo-Owned Artifacts

### Stronger distribution artifacts

- `plugins/notestorelab-codex-plugin/`
- `plugins/notestorelab-claude-plugin/`
- `plugins/notestorelab-openclaw-bundle/`
- `.claude-plugin/marketplace.json`
- `server.json`
- `scripts/release/build_distribution_bundles.py`

### Onboarding starter artifacts

- `starter-bundles/codex/`
- `starter-bundles/claude-code/`
- `starter-bundles/openclaw/`
- `scripts/release/build_starter_bundles_bundle.py`

## Proof Loops

### Common proof path

```bash
./.venv/bin/notes-recovery demo
./.venv/bin/notes-recovery ask-case --demo --question "What should I inspect first?"
./.venv/bin/notes-recovery-mcp --help
```

### Claude Code plugin validation

```bash
claude plugin validate plugins/notestorelab-claude-plugin
claude plugin validate .
```

### Distribution archive build

```bash
./.venv/bin/python scripts/release/build_distribution_bundles.py --out-dir ./dist
./.venv/bin/python scripts/release/build_starter_bundles_bundle.py --out ./dist/notestorelab-host-starters.zip
```

### MCP Registry listing boundary

`server.json` is only the metadata side of the MCP Registry story.

The referenced `pypi` package for this repository already exists on PyPI.

That means the remaining boundary is no longer "publish the package first."
The remaining boundary is external: registry submission, listing, and fresh
read-back.

The repo-side proof command below is still useful because it checks that the
metadata continues to point at the expected package surface. Passing it does
not prove that the MCP Registry has accepted, listed, or rendered the entry.

The repo-side publish-readiness proof command is:

```bash
./.venv/bin/python scripts/release/check_pypi_publish_readiness.py
```

## Allowed Claims

- "registry metadata draft shipped"
- "registry metadata points at the live PyPI package"
- "public-ready Codex plugin bundle shipped"
- "submit-ready Claude Code marketplace artifact shipped"
- "OpenClaw-compatible bundle shipped"

## Forbidden Claims

- "officially listed" without fresh external read-back
- "MCP Registry submission completed" without fresh registry read-back
- "official Codex plugin directory listing" without OpenAI-managed listing proof
- "official Anthropic marketplace listing" without fresh marketplace read-back
- "live ClawHub listing" without fresh OpenClaw-side listing proof

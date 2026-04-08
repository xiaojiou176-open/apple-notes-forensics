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
| MCP Registry | yes, the official MCP Registry exists and is still documented as a preview surface | yes: `server.json` and `notes-recovery-mcp` | not confirmed | live PyPI package now exists at `apple-notes-forensics==0.1.0.post1`, with fresh JSON read-back and install smoke; `server.json` is aligned with that live package version, but MCP Registry listing itself is still not confirmed without fresh registry read-back |
| Codex | yes, the official Codex plugin directory exists, but third-party official-directory submission is still coming soon | yes: `plugins/notestorelab-codex-plugin/` | not confirmed | public-ready Codex plugin bundle shipped; do not claim official Codex directory listing |
| Claude Code | yes, official plugin and marketplace surfaces exist | yes: `plugins/notestorelab-claude-plugin/` plus root `.claude-plugin/marketplace.json` | not confirmed | submit-ready Claude Code marketplace artifact shipped; do not claim Anthropic-managed listing without fresh read-back |
| OpenClaw | yes, the official ClawHub public registry exists | yes: `plugins/notestorelab-openclaw-bundle/` | not confirmed | public-ready compatible bundle shipped; do not claim live ClawHub or official OpenClaw listing |

## Repo-Owned Artifacts

### Stronger distribution artifacts

- `plugins/notestorelab-codex-plugin/`
- `plugins/notestorelab-claude-plugin/`
- `plugins/notestorelab-openclaw-bundle/`
- `skills/notestorelab-case-review/`
- `.claude-plugin/marketplace.json`
- `server.json`
- `scripts/release/build_distribution_bundles.py`
- `Dockerfile`

### Onboarding starter artifacts

- `starter-bundles/codex/`
- `starter-bundles/claude-code/`
- `starter-bundles/openclaw/`
- `scripts/release/build_starter_bundles_bundle.py`

## Independent Skill Surface

The canonical independent skill surface now lives at
`skills/notestorelab-case-review/`.

That directory is the single repo-owned SSOT for the skill package:

- `SKILL.md` is the canonical operator guidance
- `manifest.yaml` is the canonical publish/readiness metadata
- plugin and starter skill files are derived host copies, not parallel SSOTs

This means the repository can now truthfully say "independent skill surface
shipped" or "independent skill ready" without claiming any official directory
listing.

## Package Surface

The canonical installable package surface for this repository is PyPI:

- package name: `apple-notes-forensics`
- live package truth comes from PyPI JSON read-back plus install smoke
- `server.json` points at the PyPI package because the current MCP publication
  story is Python-first

There is no tracked npm package surface in the current public contract:

- no `package.json`
- no npm install path in the public docs
- no shipped TypeScript SDK or generated client surface yet

That means npm is not a missing canonical package lane for this repository
today. If a future npm surface ever ships, it must become an explicit new
public contract rather than an implied comparison path.

## Container Surface

Docker-ready local container surface shipped:

- `Dockerfile`
- `.dockerignore`
- `scripts/release/check_docker_surface.py`

This container path is for local reproducibility of the CLI and stdio MCP
surface. It is not proof of a hosted deployment, multi-tenant backend, or live
Glama listing.

The canonical live-image target, if and when fresh publish proof exists, is:

- `ghcr.io/xiaojiou176-open/apple-notes-forensics:0.1.0.post1`
- optional convenience tag: `ghcr.io/xiaojiou176-open/apple-notes-forensics:latest`

Do not claim a live OCI image without fresh GHCR push read-back and pull/read
verification.

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

`server.json` is still only the metadata side of the MCP Registry story.

Fresh PyPI read-back now confirms that PyPI serves
`apple-notes-forensics==0.1.0.post1`, and fresh install smoke confirms that the
published package is installable. That does **not** prove that the MCP
Registry, or any other official directory, has accepted, listed, or rendered
the package.

The repo-side publish-readiness proof command is:

```bash
./.venv/bin/python scripts/release/check_pypi_publish_readiness.py
```

## Allowed Claims

- "live PyPI package `apple-notes-forensics==0.1.0.post1` verified with fresh JSON read-back"
- "`server.json` is aligned with the live PyPI version `0.1.0.post1`"
- "PyPI is the canonical installable package surface for this repository today"
- "public-ready Codex plugin bundle shipped"
- "submit-ready Claude Code marketplace artifact shipped"
- "OpenClaw-compatible bundle shipped"
- "independent skill surface shipped"
- "Docker-ready local container surface shipped"
- "`ghcr.io/xiaojiou176-open/apple-notes-forensics` is the canonical live-image target, but live-image claims still require fresh GHCR push and pull read-back"

## Forbidden Claims

- "officially listed" without fresh external read-back
- "MCP Registry submission completed" without fresh registry read-back
- "registry metadata proves MCP Registry listing" without fresh registry read-back
- "official Codex plugin directory listing" without OpenAI-managed listing proof
- "official Anthropic marketplace listing" without fresh marketplace read-back
- "live ClawHub listing" without fresh OpenClaw-side listing proof
- "official npm package" or "npm is the canonical install path" without a real shipped npm package surface
- "officially listed skill" without fresh host-side read-back
- "hosted service" or "multi-tenant platform" for the Docker surface

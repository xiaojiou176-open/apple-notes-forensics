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
| MCP Registry | yes, the official MCP Registry exists and is still documented as a preview surface | yes: `server.json` and `notes-recovery-mcp` | not confirmed | registry metadata draft shipped; `server.json` records the intended PyPI package identifier/version, but the package is not yet confirmed live on PyPI. Do not claim submission success, listing, or package availability without fresh PyPI and registry read-back |
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

## Container Surface

Docker-ready local container surface shipped:

- `Dockerfile`
- `.dockerignore`
- `scripts/release/check_docker_surface.py`

This container path is for local reproducibility of the CLI and stdio MCP
surface. It is not proof of a hosted deployment, multi-tenant backend, or live
Glama listing.

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

Right now, that file should be treated as a submission draft, not as proof that
PyPI already serves `apple-notes-forensics`.

The repo-side proof command below checks metadata alignment plus
build-and-`twine` readiness before an owner-side publish step. Passing it does
not prove that PyPI, the MCP Registry, or any official directory has accepted,
listed, or rendered the package.

The repo-side publish-readiness proof command is:

```bash
./.venv/bin/python scripts/release/check_pypi_publish_readiness.py
```

## Allowed Claims

- "registry metadata draft shipped"
- "`server.json` records the intended PyPI package identifier and version"
- "public-ready Codex plugin bundle shipped"
- "submit-ready Claude Code marketplace artifact shipped"
- "OpenClaw-compatible bundle shipped"
- "independent skill surface shipped"
- "Docker-ready local container surface shipped"

## Forbidden Claims

- "officially listed" without fresh external read-back
- "MCP Registry submission completed" without fresh registry read-back
- "PyPI package already exists" without fresh PyPI read-back
- "registry metadata points at the live PyPI package" without fresh PyPI read-back
- "official Codex plugin directory listing" without OpenAI-managed listing proof
- "official Anthropic marketplace listing" without fresh marketplace read-back
- "live ClawHub listing" without fresh OpenClaw-side listing proof
- "officially listed skill" without fresh host-side read-back
- "hosted service" or "multi-tenant platform" for the Docker surface

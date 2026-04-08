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
| MCP Registry | yes, the official MCP Registry exists and is still documented as a preview surface | yes: `server.json` and `notes-recovery-mcp` | yes | live PyPI package now exists at `apple-notes-forensics==0.1.0.post1`, `server.json` is aligned with that live package version, and the official MCP Registry now returns `io.github.xiaojiou176-open/notestorelab-mcp` as an active listing with fresh read-back |
| Codex | yes, the official Codex plugin directory exists, but third-party official-directory submission is still coming soon | yes: `plugins/notestorelab-codex-plugin/` | not confirmed | public-ready Codex plugin bundle shipped; do not claim official Codex directory listing |
| Claude Code | yes, official plugin and marketplace surfaces exist | yes: `plugins/notestorelab-claude-plugin/` plus root `.claude-plugin/marketplace.json` | not confirmed | submit-ready Claude Code marketplace artifact shipped; do not claim Anthropic-managed listing without fresh read-back |
| OpenClaw | yes, the official ClawHub public registry exists | yes: `plugins/notestorelab-openclaw-bundle/` | not confirmed | public-ready compatible bundle shipped; do not claim live ClawHub or official OpenClaw listing |
| OpenHands/extensions | yes, the official OpenHands public extensions registry exists | yes: `public-skills/notestorelab-case-review/` plus canonical `skills/notestorelab-case-review/` | not confirmed | OpenHands/extensions-friendly public skill folder shipped; do not claim a live OpenHands/extensions listing without fresh PR/read-back |
| Glama | yes, the public Add Server and hosted MCP surface exists | yes: `glama.json`, `Dockerfile`, and the canonical GHCR target | not confirmed | repo-owned Glama-ready metadata and Docker surface shipped; do not claim a live Glama listing without fresh Glama-side read-back |
| Docker MCP Catalog | yes, the official curated Docker MCP Catalog exists | yes: `Dockerfile`, `scripts/release/check_docker_surface.py`, and the canonical GHCR target | not confirmed | Docker-ready local container surface shipped; do not claim a live Docker catalog listing without fresh Docker-side submission/read-back |

## Repo-Owned Artifacts

### Stronger distribution artifacts

- `plugins/notestorelab-codex-plugin/`
- `plugins/notestorelab-claude-plugin/`
- `plugins/notestorelab-openclaw-bundle/`
- `skills/notestorelab-case-review/`
- `public-skills/notestorelab-case-review/`
- `.claude-plugin/marketplace.json`
- `glama.json`
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

For public skill-folder registries, the portable listing packet now lives at
`public-skills/notestorelab-case-review/`.

That packet is intentionally separate from the canonical skill SSOT:

- canonical truth still lives in `skills/notestorelab-case-review/`
- the public packet adds semver-ready listing metadata for ClawHub-style
  publication
- the public packet adds an OpenHands/extensions-facing README so external
  reviewers do not need to infer the install story from internal bundle paths

## Package Surface

The canonical installable package surface for this repository is PyPI:

- package name: `apple-notes-forensics`
- live package truth comes from PyPI JSON read-back plus install smoke
- `server.json` points at the PyPI package because the current MCP publication
  story is Python-first
- this is the intended PyPI package identifier and version for the current repo
  contract: `apple-notes-forensics==0.1.0.post1`

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
surface. A live GHCR image is now verified with fresh push, manifest, pull, and
demo read-back. That is still not proof of a hosted deployment, multi-tenant
backend, live Glama listing, or Docker MCP Catalog listing.

The canonical live-image target, if and when fresh publish proof exists, is:

- `ghcr.io/xiaojiou176-open/apple-notes-forensics:0.1.0.post1`
- optional convenience tag: `ghcr.io/xiaojiou176-open/apple-notes-forensics:latest`

A live OCI image is now confirmed at:

- `ghcr.io/xiaojiou176-open/apple-notes-forensics:0.1.0.post1`
- `ghcr.io/xiaojiou176-open/apple-notes-forensics:latest`

The verified current digest is:

- `sha256:c1267822e3966fbc22f3a3a996a4b0cae67c2df8d94d35b14f93c5a90d9aab40`

`glama.json` is now the repo-owned metadata side of the Glama story. It makes
the intended maintainer identity explicit, but it does **not** prove a live
Glama listing or hosted deployment by itself.

Do not claim a live Glama listing without fresh Glama-side read-back.

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

`server.json` is the metadata side of the MCP Registry story, and that story is
now live for the current version.

Fresh PyPI read-back confirms that PyPI serves
`apple-notes-forensics==0.1.0.post1`, fresh install smoke confirms that the
published package is installable, and fresh registry read-back confirms that
the official MCP Registry now returns
`io.github.xiaojiou176-open/notestorelab-mcp` as an active listing for
`0.1.0.post1`.

The repo-side publish-readiness proof command is:

```bash
./.venv/bin/python scripts/release/check_pypi_publish_readiness.py
```

## Allowed Claims

- "live PyPI package `apple-notes-forensics==0.1.0.post1` verified with fresh JSON read-back"
- "`server.json` is aligned with the live PyPI version `0.1.0.post1`"
- "PyPI is the canonical installable package surface for this repository today"
- "official MCP Registry listing is live for `io.github.xiaojiou176-open/notestorelab-mcp` at `0.1.0.post1`"
- "public-ready Codex plugin bundle shipped"
- "submit-ready Claude Code marketplace artifact shipped"
- "OpenClaw-compatible bundle shipped"
- "independent skill surface shipped"
- "OpenHands/extensions-friendly public skill folder shipped"
- "repo-owned Glama-ready metadata shipped"
- "Docker-ready local container surface shipped"
- "live GHCR image verified at `ghcr.io/xiaojiou176-open/apple-notes-forensics:0.1.0.post1` and `:latest`"

## Forbidden Claims

- "officially listed" without fresh external read-back
- "MCP Registry submission completed" without fresh registry read-back
- "registry metadata proves MCP Registry listing" without fresh registry read-back
- "official Codex plugin directory listing" without OpenAI-managed listing proof
- "official Anthropic marketplace listing" without fresh marketplace read-back
- "live ClawHub listing" without fresh OpenClaw-side listing proof
- "live OpenHands/extensions listing" without fresh OpenHands PR/read-back
- "official npm package" or "npm is the canonical install path" without a real shipped npm package surface
- "officially listed skill" without fresh host-side read-back
- "hosted service" or "multi-tenant platform" for the Docker surface

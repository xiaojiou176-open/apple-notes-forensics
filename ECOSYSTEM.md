# Ecosystem Fit

This file explains where NoteStore Lab fits in the current AI / agent / MCP
ecosystem without overstating what is actually shipped.

## Binding Matrix

| Ecosystem | Recommended binding level | Why | Repo-side evidence |
| --- | --- | --- | --- |
| MCP | Primary | MCP is a real shipped surface, not a future placeholder | `notes-recovery-mcp`, `notes_recovery/mcp/server.py`, README protocol section |
| Codex | Primary | the repo already exposes a local MCP surface, stable review-safe artifacts, and a tracked Codex plugin bundle | `notes-recovery-mcp`, `review_index.md`, manifests, `plugins/notestorelab-codex-plugin/` |
| Claude Code | Primary | same reason as Codex, plus a tracked marketplace-ready plugin that matches Claude Code's public plugin surface | README, `notes-recovery-mcp`, `ai-review`, `ask-case`, `.claude-plugin/marketplace.json`, `plugins/notestorelab-claude-plugin/` |
| OpenHands | Secondary / comparison | the repo can be consumed by local agents, but it does not ship a dedicated OpenHands integration contract | CLI + MCP are real; no OpenHands-specific runner or docs surface |
| OpenCode | Secondary / comparison | the repo exposes a clean local tool / MCP story, but no dedicated OpenCode-specific integration layer | CLI + MCP are real; no OpenCode-specific contract or SDK |
| OpenClaw | Public-ready compatible bundle | OpenClaw can consume the shipped compatible bundle archive, but this repo still does not claim a live ClawHub listing | `scripts/release/build_distribution_bundles.py`, `DISTRIBUTION.md` |

## What Is True Today

- This repository is **AI-adjacent in a real way**, because it ships:
  - AI-assisted review
  - evidence-backed case Q&A
  - a local read-mostly MCP server
- This repository is **not** a generic agent platform.
- This repository is **not** a hosted AI service.

## What Builders Can Reliably Count On

- copied-evidence case roots
- stable manifest and review-surface filenames
- AI outputs that stay on derived artifacts first
- a local MCP entrypoint
- Codex / Claude Code plugin artifacts
- an OpenClaw-compatible bundle path that keeps the claim boundary explicit

## What Builders Must Not Assume

- no HTTP API
- no generated client
- no write-capable MCP by default
- no hosted review backend
- no generic “works with every agent framework” promise
- no live ClawHub listing today

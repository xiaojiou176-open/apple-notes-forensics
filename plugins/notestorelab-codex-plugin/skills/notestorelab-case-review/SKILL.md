---
name: notestorelab-case-review
description: Guide Codex through one bounded NoteStore Lab case review workflow.
---

Use this plugin only for NoteStore Lab case-root review work.

Core rules:

- recovery is the main product
- AI is the review layer, not the recovery engine
- one case root at a time
- prefer `review_index.md`, manifests, verification outputs, timeline, and AI review artifacts before deeper speculation
- do not treat the live Notes store as an MCP target

Suggested workflow:

1. Read `review_index.md`.
2. Read the verification preview and pipeline summary.
3. Use `ask-case` for one bounded operator question.
4. Use `case-diff` only when you are comparing two case roots.
5. Use `public-safe-export` when you need a shareable bundle instead of exposing the forensic-local case root.

# NoteStore Lab OpenClaw-Compatible Bundle

This directory is a comparison-path companion bundle for OpenClaw-style hosts.

It is intentionally not an official OpenClaw listing. Instead, it packages the
same bounded NoteStore Lab MCP launcher, plus a workspace skill, into one
portable bundle shape after the local copy-first lab already makes sense.

## What it includes

- `.claude-plugin/plugin.json`
- `.mcp.json`
- `bin/notestorelab-mcp`
- `workspace/skills/notestorelab/SKILL.md`

## Required environment

Set these before you use the launcher:

- `NOTESTORELAB_REPO_ROOT`
- `NOTESTORELAB_CASE_DIR`
- optional: `NOTESTORELAB_PYTHON`

The launcher uses `NOTESTORELAB_PYTHON` when present. Otherwise it falls back
to `$NOTESTORELAB_REPO_ROOT/.venv/bin/python`.

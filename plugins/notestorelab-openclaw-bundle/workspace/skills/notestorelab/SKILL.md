# NoteStore Lab

Use this skill when OpenClaw is helping with Apple Notes recovery cases through
the NoteStore Lab MCP surface.

## Boundary

- Stay on copied evidence only.
- Prefer derived artifacts (`review_index`, verification outputs, pipeline
  summaries, AI review outputs) before raw copied evidence.
- Do not turn this into browser control, host cleanup, or a hosted portal.

## Exact MCP entrypoint

```bash
.venv/bin/python -m notes_recovery.mcp.server --case-dir ./output/Notes_Forensics_<run_ts>
```

## Fast proof path

1. `notes-recovery demo`
2. `notes-recovery ask-case --demo --question "What should I inspect first?"`
3. Register or launch the exact MCP command above against one case root

## Truth language

- Good: "OpenClaw comparison starter bundle shipped"
- Good: "comparison-path public-ready artifact"
- Forbidden: "official OpenClaw listing"
- Forbidden: "first-class OpenClaw platform integration"

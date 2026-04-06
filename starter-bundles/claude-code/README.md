# Claude Code Marketplace Starter

This directory is a repo-owned Claude Code starter that matches the current
official plugin and marketplace surfaces:

- a marketplace root at `.claude-plugin/marketplace.json`
- a plugin manifest at `plugins/notestorelab/.claude-plugin/plugin.json`
- a bundled MCP config at `plugins/notestorelab/.mcp.json`
- a bundled skill that teaches NoteStore Lab how to stay on copied evidence

## Install path

Local validation first:

```bash
claude plugin validate starter-bundles/claude-code
claude plugin validate starter-bundles/claude-code/plugins/notestorelab
```

Session-local plugin loading:

```bash
claude --plugin-dir starter-bundles/claude-code/plugins/notestorelab --help
```

This starter matches the official plugin and marketplace surfaces, but it does
not claim live marketplace listing.

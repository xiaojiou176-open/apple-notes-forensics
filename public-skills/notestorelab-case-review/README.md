# NoteStore Lab Case Review Public Skill

This folder is the OpenHands/extensions-friendly and ClawHub-style public skill
packet for NoteStore Lab.

## What this skill teaches an agent

This is not just a label for Apple Notes. It teaches an agent four concrete
things:

1. how to install or launch the NoteStore Lab MCP surface
2. how to prove the review flow on public-safe demo artifacts first
3. how to review one copied case root without touching the live Notes store
4. how to ask bounded questions from derived artifacts instead of guessing

## What this packet includes

- `SKILL.md`
  - the concise skill entry point for progressive disclosure
- `manifest.yaml`
  - listing metadata for ClawHub-style publication
- `references/install-and-mcp.md`
  - exact install and MCP wiring examples
- `references/usage-and-proof.md`
  - first-success flow, real prompts, and proof/demo links

## First-success path

If a reviewer wants to understand the skill quickly, use this order:

1. read `SKILL.md`
2. open `references/install-and-mcp.md`
3. run the public-safe proof path from `references/usage-and-proof.md`
4. inspect the public proof links before claiming anything is officially listed

## Demo / proof links

- Landing: https://xiaojiou176-open.github.io/apple-notes-forensics/
- Public proof: https://github.com/xiaojiou176-open/apple-notes-forensics/blob/main/proof.html
- Builder guide: https://github.com/xiaojiou176-open/apple-notes-forensics/blob/main/INTEGRATIONS.md
- Releases: https://github.com/xiaojiou176-open/apple-notes-forensics/releases

## Best-fit hosts

- OpenHands/extensions contribution flow
- ClawHub-style skill publication
- repo-local skill import flows that expect a standalone folder
- any MCP-aware host that can launch a local stdio server on one explicit case
  root

## What this packet must not claim

- no official OpenHands/extensions listing without fresh PR/read-back
- no live ClawHub listing without fresh host-side read-back
- no hosted Glama deployment, Docker catalog listing, or remote MCP lane
- no direct mutation of the live Apple Notes store

## Source of truth

The canonical skill text still lives at:

- `skills/notestorelab-case-review/SKILL.md`

This folder is a public-facing derived packet. If the canonical skill changes,
copy the updated `SKILL.md` here before publishing.

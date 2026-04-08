# NoteStore Lab Case Review Public Skill

This folder is the OpenHands/extensions-friendly and ClawHub-style public skill
packet for NoteStore Lab.

## Purpose

Use it when you want one portable skill folder that keeps the NoteStore Lab
case-review story honest:

- one bounded case root at a time
- copied evidence only
- derived artifacts first
- local stdio MCP instead of a hosted Notes platform claim

## What this packet includes

- `SKILL.md`
  - the canonical case-review instructions copied from the repo SSOT skill
- `manifest.yaml`
  - repo-owned listing metadata for ClawHub-style skill publication

## Best-fit hosts

- OpenHands/extensions contribution flow
- ClawHub-style skill publication
- repo-local skill import flows that expect a standalone folder

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

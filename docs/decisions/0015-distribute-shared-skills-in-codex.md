<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 15. Distribute shared skills in Codex

- Status: accepted
- Date: 2026-11-22
- Issue: #8

## Context

The existing Claude Code plugin distributes the application skills from
the repository. Codex users need to install the same skills and keep them
aligned with the application version.

## Decision

The portable `plugin.json` at the repository root uses the existing
`skills/` directory. The repository marketplace at
`.agents/plugins/marketplace.json` points at the same root. Update both
plugin manifests with the application version. The development skill is
discovered separately from `.agents/skills/`.

## Alternatives

A Codex-specific compatibility manifest would depend on a second format
for Codex users. Copying skills to a dedicated plugin subdirectory would
introduce duplicate content or require a build step.

## Consequences

The same user skill documents setup for either client. The repository
catalogue supports distribution without a separate marketplace repository.
The release process must keep the Python package and both manifests on
equivalent versions. Repository catalogues are available on supported
Codex clients.

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# my-beautiful-choir

Choir management application delivered only as an MCP app (MCP server with
MCP Apps views), in web mode (Streamable HTTP, accounts) and personal mode
(stdio, single local user). See [README.md](README.md) and the ADRs in
`docs/decisions/`.

Contributors follow the contribution rules below. Use the `contribute`
development skill to be guided from the issue to the pull request.

@CONTRIBUTING.md

## Project specifics

- Run every tool through `uv run --frozen`; checks are nox sessions.
- In personal mode, stdout carries the MCP protocol: never write to stdout,
  logs go to stderr.
- Never read environment configuration files (`.env` and similar); only
  their `.example` counterparts.

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# my-beautiful-choir

Read [CONTRIBUTING.md](CONTRIBUTING.md) before contributing. Use the
`contribute` development skill for the workflow from issue to pull request.

- Run development tools through `uv run --frozen`. The shared checks are
  defined in `noxfile.py`.
- In personal mode, stdout carries the MCP protocol. Send logs to stderr.
- Use only example files to inspect environment configuration. Never read
  local environment configuration or credentials.

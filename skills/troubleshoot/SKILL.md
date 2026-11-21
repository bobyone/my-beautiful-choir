---
name: troubleshoot
description: Use when my-beautiful-choir does not start, does not appear in the MCP client, shows an error, or when someone asks what an error code such as MBC-CONFIG, MBC-PORT, MBC-INSTALL or MBC-UNEXPECTED means, or where to find its logs.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Troubleshoot my-beautiful-choir

The reference is `docs/how-to/troubleshoot-startup.md` in the repository.

## 1. Get the startup message

When my-beautiful-choir cannot start, it writes on stderr a message such as
`my-beautiful-choir could not start [MBC-CONFIG]: ...`, followed by what to
do, and exits with a non-zero code.

Find it, depending on where it runs:

- **personal mode in Claude Desktop**: the `mcp-server-my-beautiful-choir.log`
  file in Claude's log folder (*Settings → Developer → Open logs folder*);
- **personal mode in VS Code**: *MCP: List Servers* → my-beautiful-choir →
  *Show Output*;
- **web mode with Docker Compose**: run `docker compose logs my-beautiful-choir`;
- **anywhere**: run the client's command in a terminal, for instance
  `uv run --directory <clone> my-beautiful-choir`, to see the message
  directly; stop it with Ctrl+C.

Ask the user to paste the message. Never read `.env` files; ask for the
values of `MBC_` keys if needed, and remind the user not to paste secrets.

## 2. Apply the fix for the error code

| Code | Exit code | Fix |
|---|---|---|
| `MBC-CONFIG` | 2 | Correct each key listed in the message; valid values are in `docs/configuration.md`. |
| `MBC-PORT` | 3 | Another program uses the web mode port: stop it, or set `MBC_WEB__PORT` to a free port. |
| `MBC-INSTALL` | 4 | A view is missing: from the clone, run `uv run nox -s ui`, then restart. |
| `MBC-UNEXPECTED` | 1 | A bug: get the `exc_info` field of the `startup_failed` log record, then use the `report-issue` skill. |

## 3. Other symptoms

- **The tool works but no view is displayed**: the MCP client may not
  support MCP Apps; the text result is still valid.
- **Web mode answers 421 on `/mcp`**: the `Host` header is not allowed; add
  the public `host:port` to `MBC_WEB__ALLOWED_HOSTS`.
- **More details are needed**: set `MBC_LOG_LEVEL=DEBUG`, then restart.

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# How to troubleshoot a startup failure

When my-beautiful-choir cannot start, it writes a message on stderr, then
stops with a non-zero exit code. The message says what failed, why, and how
to fix it, with a stable error code:

```text
my-beautiful-choir could not start [MBC-CONFIG]: invalid configuration.
  - MBC_WEB__PORT: '90000' is not valid: Input should be less than or equal to 65535
Fix the values listed above, then restart.
See https://github.com/bobyone/my-beautiful-choir/blob/main/docs/how-to/troubleshoot-startup.md
```

The same failure is also logged as a JSON record whose `message` is
`startup_failed`, with `error_code` and `exit_code` fields.

## 1. Find the message

| Where my-beautiful-choir runs | Where to read stderr |
|---|---|
| Personal mode, in Claude Desktop | The `mcp-server-my-beautiful-choir.log` file in Claude's log folder (*Settings → Developer → Open logs folder*). |
| Personal mode, in VS Code | Command palette → *MCP: List Servers* → my-beautiful-choir → *Show Output*. |
| Personal mode, other MCP clients | The client's MCP server logs; or run the command below in a terminal. |
| Web mode, with Docker Compose | `docker compose logs my-beautiful-choir` |

To see the message directly, run the same command as the MCP client in a
terminal, for example `uvx my-beautiful-choir`, or
`uv run my-beautiful-choir` from a clone of the repository. In personal
mode, stop it with Ctrl+C (or Ctrl+Z then Enter on Windows) once it is
started.

## 2. Fix according to the error code

| Error code | Exit code | Cause | Fix |
|---|---|---|---|
| `MBC-CONFIG` | 2 | An option or an `MBC_` environment variable is invalid. Every invalid key is listed. | Correct the listed keys; see the [configuration reference](../configuration.md). |
| `MBC-PORT` | 3 | Web mode cannot listen on the configured address and port, usually because another program uses the port. | Stop the other program, or set another port with `MBC_WEB__PORT`. |
| `MBC-INSTALL` | 4 | A view of the user interface is missing from the installation. | Reinstall my-beautiful-choir. From a clone of the repository, build the user interface first: `uv run nox -s ui`. |
| `MBC-UNEXPECTED` | 1 | An unexpected error, most likely a bug. | Read the `exc_info` field of the `startup_failed` log record, then [report the problem](https://github.com/bobyone/my-beautiful-choir/issues/new/choose), without secrets or personal data. |

## 3. Get more details

Set `MBC_LOG_LEVEL=DEBUG` to log more details, then restart.

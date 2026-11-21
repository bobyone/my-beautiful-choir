<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Configuration reference

The configuration is read once, at startup, from the command line and from
environment variables prefixed with `MBC_`. Nested keys use a double
underscore (`MBC_WEB__PORT`). Names are case-insensitive.

A command-line option takes precedence over the matching environment
variable. An empty variable is ignored: the default value applies.

If any value is invalid, the application does not start: it lists every
invalid key with the expected value on stderr and exits with code 2 (see
[troubleshooting](how-to/troubleshoot-startup.md)).

## Command line

| Option | Description |
|---|---|
| `--mode {personal,web}` | Running mode; overrides `MBC_MODE`. |
| `--version` | Prints the version and exits. |
| `--help` | Prints the usage and exits. |

## Keys

| Key | Type | Default | Required | Description |
|---|---|---|---|---|
| `MBC_MODE` | `personal` \| `web` | `personal` | no | Running mode: personal mode over stdio, or web mode over HTTP. |
| `MBC_LOG_LEVEL` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL` | `INFO` | no | Minimum level of the logs written to stderr. |
| `MBC_DATA_DIR` | directory path | the user data directory of the platform (`%LOCALAPPDATA%\my-beautiful-choir` on Windows, `~/Library/Application Support/my-beautiful-choir` on macOS, `~/.local/share/my-beautiful-choir` on Linux) | no | Personal mode: directory of the database and the scores; created at startup if needed. |
| `MBC_WEB__HOST` | IP address or host name | `127.0.0.1` | no | Web mode: address to listen on. Use `0.0.0.0` in a container. |
| `MBC_WEB__PORT` | integer from 1 to 65535 | `9000` | no | Web mode: port to listen on. |
| `MBC_WEB__ALLOWED_HOSTS` | comma-separated list of `host:port` | empty | no | Web mode: `Host` header values accepted, as a protection against DNS rebinding. Empty means the local host only. Required when listening on `0.0.0.0`. |

Keys starting with `MBC_WEB__` are ignored in personal mode. Set them one
by one: a `MBC_WEB` variable is invalid.

## With Docker Compose

`compose.yaml` reads `.env` when it exists, but always sets `MBC_MODE=web`,
`MBC_WEB__HOST=0.0.0.0` and `MBC_WEB__PORT=9000` inside the container; the
port is published on `127.0.0.1:9000` only. `MBC_WEB__ALLOWED_HOSTS`
defaults to `localhost:9000`.

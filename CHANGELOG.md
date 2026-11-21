<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial architecture decision records (#1).
- Repository foundation: editor and Git configuration, Python project with
  uv, nox sessions shared by the pre-commit hook and CI, REUSE compliance,
  community files, Claude Code plugin skeleton and settings (#1).
- Application skeleton (#1):
  - personal mode over stdio and web mode over Streamable HTTP, selected
    with `--mode` or `MBC_MODE`;
  - configuration from `MBC_` environment variables, validated at startup;
  - `show_about` tool with its "About" MCP Apps view, translated into the
    official languages of European states (machine translations to be
    reviewed);
  - web mode health check (`/healthz`), Prometheus metrics (`/metrics`),
    JSON logs with correlation ids and without client IP addresses, DNS
    rebinding protection;
  - startup error messages with stable error codes and exit codes;
  - container image and Compose file for web mode.
- Plugin skills: install, troubleshoot, privacy, report an issue (#1).
- Personal mode keeps its data in a SQLite database in the user data
  directory, set with `MBC_DATA_DIR`; an unusable directory or a failed
  migration stops the startup with `MBC-DATA` (exit code 5) (#7).
- Choirs in personal mode: create, rename, list, and choose the default
  choir (#7).
- Works in personal mode: add and edit the works of a choir's repertoire,
  searched ignoring case and accents (#7).
- Plugin skills: manage choirs, manage works (#7).

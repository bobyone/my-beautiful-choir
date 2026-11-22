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

- Codex contribution guidance, a contribution skill and repository protection
  settings backed by shared Claude Code and Codex rules. The assistant
  hooks run offline without relying on the shared uv cache. The shared
  rules account for Bash and PowerShell line continuations (#8).
- Codex plugin catalogue exposing the shared user skills (#8).

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

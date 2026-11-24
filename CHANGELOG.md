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

### Fixed

- Keep temporary copies of opened scores in a private directory (#7).
- Require a fresh confirmation if a deletion preview changes (#7).

### Added

- Transcribe PDFs with multiple movements in personal mode. The application
  adds one MusicXML score per movement in source order and publishes the
  results together (#23).
- Transcribe a stored PDF into MusicXML in personal mode, from the Work
  view or directly through MCP. Discover Audiveris automatically and allow
  the model to add and read MusicXML text and verify against PDF pages (#20).
- `get_score_file` gives a score back in the conversation as an embedded
  file, up to the 50 MB score maximum (#15, #18).
- Download of scores from the Work view, in clients that can save files (#15).

- Repertoire pages of 10 works by default in the Repertoire view and
  `show_repertoire`, with `page` and `page_size` arguments (#13).

- Python installers for Claude Desktop and ChatGPT desktop with local Codex (#11).

- Repertoire and Work views in personal mode with choir switching, title
  and composer search, and score upload, opening and confirmed deletion (#7).

- Confirmed deletion of choirs, works and scores in personal mode, with a
  localized Deletion view when the MCP host cannot ask directly (#7).

- Codex contribution guidance, a contribution skill and repository protection
  settings backed by shared Claude Code and Codex rules. The assistant
  hooks run offline without relying on the shared uv cache. The shared
  rules account for Bash and PowerShell line continuations. The Codex
  permissions profile protects named environment files while preserving
  access to examples (#8).
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
- Personal mode keeps its data in a SQLite database in the user data
  directory, set with `MBC_DATA_DIR`; an unusable directory or a failed
  migration stops the startup with `MBC-DATA` (exit code 5) (#7).
- Choirs in personal mode: create, rename, list, and choose the default
  choir (#7).
- Works in personal mode: add and edit the works of a choir's repertoire,
  searched ignoring case and accents (#7).
- Scores in personal mode: add a score to a work from a local file or a
  public Google Drive link (PDF, MusicXML, compressed MusicXML, MuseScore,
  up to 50 MB, recognized from the file content), and open a copy of it
  with the default application of the computer (#7).
- Plugin skills: manage choirs, manage works, manage scores (#7).

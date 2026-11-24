<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 21. Run local score recognition

- Status: accepted
- Issue: #20

## Context

Users want to transcribe a stored PDF from the Work view or directly from
the conversation in personal mode. A PDF can contain several pages and
recognition can take longer than a tool request.

## Decision

An asynchronous transcription service depends on a ScoreRecognizer.
Its first adapter runs separately installed Audiveris in batch mode.
Discovery uses Windows registry entries, standard installation paths and
PATH on Windows, application bundles and Spotlight on macOS, and standard
paths, PATH and Flatpak on Linux. A configured executable takes precedence.
Use a private workspace and accept only one complete MusicXML export.
Check the engine's book metadata because a successful export can omit an
invalid sheet. SQLite retains the link from each transcription to its source.

The view and conversation use the same start and status operations. Job
status is bounded and in memory. Successful results remain available
through the repertoire after restart. The most recent transcription is
returned by default and explicitly requested recomputation creates a new
score.

## Alternatives

- Oemer accepts images, so PDF rendering and combining independent outputs
  would be part of the integration.
- A synchronous tool avoids polling and depends on each MCP client's
  timeout.
- Inferring the source from a label avoids a migration and breaks after
  renaming or when the label is ambiguous.

## Consequences

Audiveris is an independent program installed by the user. Each supported
engine needs its own adapter, discovery and installation information.
Multiple movements and incomplete transcriptions fail before storage.

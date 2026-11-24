<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 23. Transcribe all movements of a source score

- Status: accepted
- Issue: #23
- Supersedes: the single-movement restriction in [ADR 0021](0021-run-local-score-recognition.md)

## Context

A stored PDF can contain several movements. Refusing these exports makes
users split a PDF that the engine can already transcribe. Movements may
share pages, and a successful exit may still leave a missing export.

## Decision

Use Audiveris's individual MusicXML exports. Check the Audiveris project
for completed sheets and the expected count, then require one export
for each movement number. Supply sources in numeric order and validate
and stage one movement at a time. The unit of work publishes the run and
its scores together. Failed writes discard the staged contents.

Store a run separately from its results. The latest run is reusable
only when every movement still exists. A new run keeps earlier scores.

MCP returns an ordered array. The legacy singular result remains present
for a single movement. The work view renders numbered labels for
multi-movement transcriptions using its locale.

## Alternatives

The MusicXML opus format wraps the movements but has limited editor
support and needs an additional extraction step before reading a
movement. Inferring the run from score labels cannot detect the loss of
all movements. A separate record keeps the expected movement count even
when every result has been deleted.

## Consequences

Existing transcriptions migrate as runs of one movement. A rollback to
the previous schema keeps the scores, their contents and provenance.
The original PDF remains available for comparison.

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# ADR 0024: List scores without opening a view

## Context

Sending a score file in the conversation requires its score ID.
`show_work` identifies the scores but also opens the Work view in hosts
that support MCP Apps. Sending scores from several works can therefore
open several views (issue #22).

## Decision

Register `list_scores` as a standalone MCP tool in personal mode, using
the same injected repertoire and score services as the existing tools.
Resolve a work by ID, title fragment or complete reference in its stored
title. Title and reference searches use the named or default choir.
When several works match, return their IDs and labels so the user can
choose. When a single work is selected, return the IDs, labels and
formats of all its scores. The existing `get_score_file` tool sends each
selected file.

## Alternatives

- Reuse `show_work`: it already exposes the score list, but its UI
  association opens a Work view even when the user only asks for files.
- Expand `find_score_sources`: it already works without a view, but
  changing its PDF-only contract would affect callers choosing a PDF
  for transcription.

## Consequences

An assistant can find and send scores from multiple works without
opening views. The Work and Repertoire views keep their existing tools
and contracts. References remain part of stored titles and require no
database migration.

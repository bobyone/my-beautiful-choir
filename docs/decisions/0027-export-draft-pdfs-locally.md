<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 27. Export draft PDFs locally

- Status: accepted
- Date: 2026-11-25
- Issue: #26 (first delivery of #25)

## Context

People can download an editable score or get a PDF for reading, printing
or sharing. A draft PDF must carry a visible watermark on every page.

## Decision

An optional local MuseScore Studio executable renders a temporary
MusicXML copy. PDFium adds a vector watermark to each page of a draft.
The tool returns a draft PDF only when all pages have been marked.
Pass only the bounded score document to the renderer, including when the
score is stored in a compressed MusicXML archive.

## Alternatives

Inserting a credit into the score and relying on the engraving engine
would depend on its page layout and could miss pages. Using a remote
renderer would require transferring score files to another service.

## Consequences

The score and its layout metadata remain in the repertoire as stored.
PDF export requires an installed engine and has a timeout. Score
documents with linked images are refused during export.

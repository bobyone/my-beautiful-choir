<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 22. Exchange score contents for verification

- Status: accepted
- Issue: #20

## Context

The user wants the model to pass MusicXML directly to the application,
read the generated XML, and compare it to the source PDF.

## Decision

Personal mode exposes standalone MCP tools to submit validated MusicXML
text, read its text in bounded slices, and render a selected source page
as a PNG image. The PDF renderer is injected separately from recognition.
Use PDFium with Pillow in the optional personal installation group.
XML parsing never resolves external entities or loads a DTD. The original
file download and opening tools keep their contracts.

## Alternatives

- Sending a whole PDF as an embedded resource depends on the host being
  able to open it and hand its pages to the model.
- Sending whole XML scores as files avoids pagination but makes text
  accessibility depend on the MCP host.
- Using the recognition engine as a page renderer ties verification to its
  installation and exports.

## Consequences

The client or model provider can receive score content when requested by
the user. A model without visual access reports what it was able to verify.

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 29. Version the measure exchange notation

- Status: accepted
- Date: 2026-11-25
- Issue: #28 (second delivery of #25)

## Context

A caller should be able to inspect a measure range with enough
information to locate and later edit its musical events.

## Decision

Use compact JSON with a numbered notation version. Represent time as
exact rational multiples of a quarter note. Carry opening attributes,
changes, written and sounding pitch information, and boundary
indications. Bound text by field and paginate the response on record
boundaries. Mark returned free text as untrusted score data.

## Alternatives

ABC is compact, but connecting lyrics to overlay voices would require
extensions. Isolated MusicXML fragments preserve familiar syntax and
would need additional work to recover their inherited context.
Unversioned text would make changes to the output difficult to detect.

## Consequences

The schema documents the read operation. The later write operation
must test that the representation can round-trip the musical details
in scope. A client can resume with the same request and score
fingerprint. A field omitted by the text policy is not available
from the MCP report.

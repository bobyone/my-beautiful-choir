<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Score exchange notation v1

The [JSON Schema](score-exchange-notation-v1.schema.json) describes the wire structure.
The `read_measures` MCP result has `notation_version: 1` and one
`pitch_mode` for all its records. A measure is a record with:

| Field | Representation |
|---|---|
| `position`, `label`, `implicit` | 1-based position, printed label and explicit implicit-measure flag. |
| `opening` | Attribute events effective before changes encoded in this measure. |
| `events` | Events in temporal order, with stable ordering in each staff and voice. |
| `incoming`, `outgoing` | Matched musical spans that cross each measure boundary. |
| `unsupported` | Source elements that could not be interpreted. |

Every event has a `kind` and a signed rational `offset` in quarter
notes, encoded as an integer or reduced fraction string. Notes and
rests have a `staff` and `voice`, and a positive rational
`duration` except for grace notes. Directions and attributes may
apply to a whole part. Details contain a kind and, when present,
`value`, ordered `properties` as name/value pairs, and nested
`details`. Supported details include chord membership, accidentals,
tuplets, lyrics, breath marks, articulation, grace, cue, pedal,
dynamics and repeat markings. Graphical position, fonts and page
breaks are excluded.

A written `pitch` is an object with `step` (A to G), `octave` and
rational `alter` in semitones. In sounding mode, `pitch` is an array
of rational semitone heights, with 60 representing C4. Doubling
produces two heights. The event still carries `written_pitch` for
spelling. When transposition cannot be determined, `pitch` is
`null` in sounding mode. A rest or unpitched event has no pitch
field. Span endpoints refer to a 1-based measure and event position
in the same part.

The output may contain an `{"omitted":true}` placeholder in place
of source text. A result with such a placeholder or unsupported
elements does not provide the omitted information for later writing.

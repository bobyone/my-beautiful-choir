<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# ADR 0032: Bound the event notes given to the model

## Context

ADR 0031 allowed event notes of up to 2,000 characters. Every event read
(`get_event`, `list_events`, and the results of the writing tools) returns
the notes to the model, in the text and in the structured content. The
project rule for MCP applications forbids passing long free text (beyond a
configurable limit, 280 characters by default) to the model without
structuring it or asking the user first. Events have no view where long
notes could stay (review of PR #32).

## Decision

- A setting, `EventSettings.notes_chars` (`MBC_EVENTS__NOTES_CHARS`,
  default 280, from 1 to 2,000), bounds the notes accepted when an event is
  created or edited.
- When stored notes are longer than the current setting (for instance after
  the setting was lowered), the event tools leave them out of both the text
  and the structured content and set `notes_withheld`; the text tells the
  model how to shorten them.
- The storage keeps its 2,000-character maximum.

## Alternatives

- Keep 2,000 characters and ask for the user's consent through elicitation
  before returning long notes: compliant, but every listing would ask, and
  hosts without elicitation could never read them.
- Structure long notes with an intermediate model: not available in the
  project yet.
- Keep long notes for a future events view only: there is no such view.

## Consequences

- Event notes are short by default; an operator who raises the limit takes
  the responsibility for longer free text reaching the model.
- Work notes (up to 2,000 characters) predate this rule and are not changed
  here.

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 28. Read a shared musical model

- Status: accepted
- Date: 2026-11-25
- Issue: #28 (second delivery of #25)

## Context

The description, range reader and comparison must agree on where a note
occurs and what notation it carries.

## Decision

Use a ScoreReader contract with a MusicXML adapter. Reuse the secured
parser and compressed container reader. Normalise partwise and timewise
scores to ordered parts, exact measure timelines and effective
attributes. Preserve staff, voice, written pitch and known notation.
Compute sounding pitch only when the score supplies the necessary
information. Keep track of unsupported content.

## Alternatives

Reading XML independently for each report would simplify a single
report at first and duplicate timing, transposition and safety checks.
Relying on a general conversion library would add a dependency and
would need a fidelity assessment for the expected formats.

## Consequences

The adapter and operations can be tested separately. New notation is
added explicitly to the reader vocabulary. Partial reading remains
visible to callers. Existing stored scores and tools retain their
formats and behaviour.

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 30. Compare musical content by matched measure

- Status: accepted
- Date: 2026-11-25
- Issue: #28 (second delivery of #25)

## Context

Raw file differences can be unrelated to music. Labels can also be
repeated or changed between two scores.

## Decision

Match unique part labels and printed measure labels, with explicit
one-to-one matches by position available to the caller. Compare
normalised musical events and markings, including differences in
written spelling at the same pitch. Report additions, removals,
changes, ambiguities and unsupported content.

## Alternatives

Comparing XML would report changes to formatting and divisions.
Automatically guessing matches for repeated or changed labels could
associate the wrong music, particularly in repeated sections.

## Consequences

The result can be partial and list ambiguous positions. The caller can
repeat the comparison with explicit matches. Layout ignored by the
reader has no effect on musical comparisons.

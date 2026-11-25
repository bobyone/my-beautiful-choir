<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 25. Persist score states and versions

- Status: accepted
- Date: 2026-11-25
- Issue: #26 (first delivery of #25)

## Context

A work can contain originals, transcriptions and revisions. A manager must
be able to work on drafts while retaining the final scores.

## Decision

Keep state, a draft revision and the final version number in the score
record. Assign final versions with a per-work counter in the same SQLite
write transaction as the insertion or finalisation. Migrate existing
records as finals in stable creation order. A duplicate gets its own
storage key and a snapshot of the originating score. Keep compressed
MusicXML intact and read its manifest-declared document for validation.

## Alternatives

Deriving the state from the label would couple writes to presentation.
Choosing the greatest surviving version number would reuse a number
after it was deleted. Keeping only a live origin reference would lose
lineage on deletion. Unpacking a duplicate could drop resources.

## Consequences

The migration only changes metadata. Drafts can be inspected and saved
independently. The former application cannot enforce the state, so a
rollback restores both database and files from a pre-migration backup.

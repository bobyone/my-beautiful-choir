<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 16. Bind confirmation to a deletion preview

- Status: accepted
- Date: 2026-11-22
- Issue: #7

## Context

ADR 0013 requires confirmation for destructive actions. Identifying
the target alone leaves a gap between presenting the deletion and
performing it. An edit or new descendant can change the deletion in
that interval, even when the displayed counts stay the same.

## Decision

A deletion preview carries the displayed summary and an immutable
snapshot of the affected records, with descendants ordered by ID.
All deletion entry points present the summary before approval. On
confirmation, the deleter checks authorization, rebuilds the preview,
and deletes only when it matches. SQLite starts the write transaction
with `BEGIN IMMEDIATE` before its first read. Read-only previews use a
consistent read transaction. File cleanup happens after the commit.

The Work and Deletion views use the same app-only confirmation tool.
For MCP clients that resume the tool with an input response, a distinct
single-use token binds the response to the original call and preview.
A changed preview requires a fresh confirmation. A missing target or
revoked access produces the existing domain error.

## Alternatives

A database revision would make comparison cheaper, but requires
a migration and updating the revision in every relevant write path.
A comparison in a separate transaction leaves room for a concurrent
write to invalidate the check before deletion.

## Consequences

Confirmation snapshots add memory and database reads in proportion to
the deletion scope. Tokens expire after ten minutes and pending
confirmations are cleared on restart. A conflicting writer may have to
wait for the SQLite write transaction. No migration is needed.

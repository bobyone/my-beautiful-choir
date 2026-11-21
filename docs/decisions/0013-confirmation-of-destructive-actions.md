<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 13. Confirmation of destructive actions

- Status: accepted
- Date: 2026-11-21
- Issue: #7

## Context

Deleting a choir, a work or a score cannot be undone. Deletions can be
requested from a view, or by the model in the conversation, possibly after
misunderstanding the user or following instructions injected in a
document. The user must confirm every deletion.

## Decision

- A tool receives a **tool context** (`Tool.execute(arguments, context)`)
  giving a `ConfirmationRequester`, which asks the user a question and
  answers `confirmed`, `refused` or `unavailable`.
- With MCP clients supporting **elicitation**, the deletion tool asks the
  user directly; a refusal deletes nothing. Up to protocol 2025-11-25, the
  question is asked during the call. From protocol 2026-07-28 (SEP-2322),
  the call ends with an input request carrying the question, and the client
  retries the call with the answer: the tool then runs twice, so a tool
  never changes anything before asking for confirmation.
- When elicitation is unavailable, the deletion is kept under a
  **single-use token**, valid 10 minutes, and the "Deletion" view shows what
  will be deleted with a button calling an app-only tool
  (`_meta.ui.visibility: ["app"]`, invisible to the model) with the token.
- Deletion buttons of the other views open a confirmation dialog, then call
  app-only tools.

The model can therefore never delete without a user action.

## Alternatives

- A `confirmed` argument set by the model after asking in the
  conversation: simple, but the model sets it itself, which protects
  neither from a misunderstanding nor from an injection.
- Deletions only from the views: safe, but the conversation could not
  delete anything.
- Soft deletion with a recycle bin: allows undoing, but adds a state to
  every element and a purge; not needed at this volume.

## Consequences

- The `Tool` contract changes: every tool receives the context, and a tool
  asking for confirmation must have no effect before the question.
- Both protocol behaviours are tested with the SDK in-memory client.
- Pending confirmations are kept in memory: they are lost when the server
  restarts, which only cancels the deletion.

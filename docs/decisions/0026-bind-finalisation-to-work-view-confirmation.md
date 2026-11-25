<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 26. Bind finalisation to Work view confirmation

- Status: accepted
- Date: 2026-11-25
- Issue: #26 (first delivery of #25)

## Context

Only the user should be able to finalise an inspected and valid draft.

## Decision

Reuse the pending confirmation store. A preview contains the score
snapshot and a digest of the validated bytes. Keep the token out of the
public result fields and give it to the Work view via result metadata.
The app-only tool checks the connection and consumes the token once.
The score service checks permissions, state, revision and contents
again before allocating the version and committing the transition.

## Alternatives

A model-callable confirmation would let the model confirm its own
request. A general text confirmation would depend on a different
interaction from the one the manager reviews in the Work view.

## Consequences

The host must route app-only calls and isolate private result metadata.
Enable finalisation for a particular local installation only after
checking that its MCP Apps host satisfies that contract. A stale
preview requires a fresh user decision.

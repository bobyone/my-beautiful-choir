<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 1. Record architecture decisions

- Status: accepted
- Date: 2026-11-21
- Issue: #1

## Context

The project is open to external contributors. They need to understand why
the architecture is what it is, and decisions must stay traceable over time.

## Decision

Every architecture decision is recorded as an Architecture Decision Record
(ADR) in `docs/decisions/`, one numbered file per decision
(`NNNN-short-title.md`), written in English, with its context, the decision,
the rejected alternatives and its consequences.

An ADR is never rewritten once accepted. A decision that changes is recorded
in a new ADR, which marks the previous one as superseded.

ADRs are committed together with the code they concern.

## Alternatives

- Design notes in issues only: decisions get lost among discussions and are
  not versioned with the code.
- A single architecture document: history of decisions is not kept.

## Consequences

- Each structuring choice made during design produces an ADR.
- Reviewers check that a pull request changing the architecture adds or
  supersedes an ADR.

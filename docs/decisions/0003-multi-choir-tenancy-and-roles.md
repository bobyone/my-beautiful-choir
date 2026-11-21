<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 3. Multi-choir tenancy and roles

- Status: accepted
- Date: 2026-11-21
- Issue: #1

## Context

A web mode instance is expected to serve several choirs (a few dozen), and
a person may sing in more than one choir.

## Decision

- A web mode instance hosts several choirs. Each choir's data is isolated:
  every query is scoped to a choir, and access is checked against the
  current user's membership.
- A user may be a member of several choirs, with one role per choir.
- Roles:
  - **instance administrator**: manages the instance, its choirs and its
    user accounts;
  - **manager** (per choir): manages the choir's repertoire, scores and
    members;
  - **chorister** (per choir): consults and downloads the choir's
    repertoire and scores.
- In personal mode, the implicit local user is manager of every choir and
  there is no instance administrator.

Authorization is an abstraction of the core; web and personal modes provide
their implementations.

## Alternatives

- One choir per instance: simpler, but each choir must deploy its own
  instance, and a person in two choirs needs two accounts.
- Only two roles (administrator and member): too coarse, a choir director
  would need instance-wide rights to edit their repertoire.

## Consequences

- Tenancy isolation is tested explicitly (a user never sees another choir's
  data).
- Finer roles (for instance, per voice part) can be added later without
  changing the model of memberships.

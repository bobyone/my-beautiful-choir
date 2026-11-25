<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# ADR 0031: Model choir events with kind-based visibility

## Context

A choir needs to manage its events (issue #30). Each event kind has its own
audience: a concert is visible to everyone, including people who are not
members of the choir, and a manager or the instance administrator can hide
its programme from the public; a rehearsal is visible to the members of the
choir; a lesson is visible to its participants and to the managers. Every
event can have a programme of repertoire works.

Accounts, memberships and members do not exist in the code yet, and no
public entry point exists. The visibility rules must nevertheless be in
place now, so that a later public MCP and the lessons (after issue #31) can
rely on them.

## Decision

- A new `events` notion holds the `Event` entity, its programme entries,
  its rules, the `Period` value object, the `EventRepository` contract and
  `EventService`.
- The event kind is fixed at creation: changing it would change the
  audience of existing data by accident.
- A programme entry refers to a work of the event's choir, or to none, and
  keeps the title of the work. The current title is shown while the work
  exists, and the kept title after its deletion.
- Who is consulting is given by a separate `ObserverSource` abstraction in
  the `authorization` notion. It returns an `Observer`: the local user, the
  instance administrator, a manager, a chorister or the public. Personal
  mode uses `LocalObserverSource`, which always returns the local user.
- What an observer sees is decided by one pure function, `visible_event`,
  applied to every event read or listed. An event the observer may not see
  is reported as not found. The public never sees the notes of a concert,
  nor its programme when it is hidden.
- Two permissions are added: `MANAGE_EVENTS` (managers) and
  `HIDE_PROGRAMME` (managers and the instance administrator). Consulting
  events uses the observer, not a permission, because the public may
  consult concerts.
- Events are listed over a period with both bounds included. The default
  period and the maximum period length are settings, in days.
- Until choir members exist, `create_event` offers only concerts and
  rehearsals, and a lesson without participants is refused.

## Alternatives

- Add an `observer` method to `Authorization`: fewer types, but it mixes
  "may this user act?" with "who is looking?", and a public entry point
  would have to implement both.
- One visibility strategy per event kind: open to new kinds, but it splits
  a single security rule over several classes, where a pure function can
  be tested exhaustively for every kind and observer.
- Read the title of a programme work at display time only: always current,
  but the programme of a past concert would lose a deleted work.
- Lesson participants as free-text names until members exist: no
  prerequisite, but it stores personal data with no link to a person and
  requires a data migration later.

## Consequences

- Personal mode sees every event; the visibility matrix is covered by unit
  tests with every kind and observer.
- A public MCP only needs an `ObserverSource` returning the public observer.
- Deleting a work keeps its programme entries, without reference; deleting a
  choir deletes its events. Both deletion previews count the events
  concerned.
- Lessons become available once choir members are delivered (issue #31).

---
name: manage-events
description: Use when a my-beautiful-choir user wants to add, change, list, read or delete an event of a choir (a concert or a rehearsal), set or change its programme of works, or hide a concert programme from the public, in personal mode.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Manage the events of a choir

Events are managed with the tools of the my-beautiful-choir MCP server, in
personal mode. An event is a concert, a rehearsal or a lesson; its kind sets
who may see it.

## Tools

| Task | Tool |
|---|---|
| Add a concert or a rehearsal | `create_event(choir?, kind, title, starts_at, ends_at?, place?, notes?, programme?)` |
| List the events of a period | `list_events(choir?, start?, end?)` |
| Read an event and its programme | `get_event(event_id)` |
| Change an event or its programme | `edit_event(event_id, ...)` |
| Hide a concert programme from the public, or show it again | `set_programme_hidden(event_id, hidden)` |
| Delete an event | `delete_event(event_id)` |

## Rules to follow

- Only the kind, the title and the start are required. Fill in only what the
  user gave; **never invent** a place, an end or a programme.
- Dates are ISO 8601 **with a time zone offset**. When the user gives a
  local time, use their time zone. Results are in UTC: always present dates
  to the user in their time zone.
- A concert is visible to everyone; a rehearsal to the members of the choir.
  Notes are short (280 characters unless configured otherwise), internal,
  and never shown to the public. Lessons cannot be
  created yet: tell the user they come with choir members.
- The kind of an event cannot change. To change it, confirm with the user,
  delete the event and create a new one.
- A programme lists works of the choir's repertoire by id, in order. Find
  the work ids with `list_scores` or `show_repertoire` (see the
  `manage-works` skill). An entry may also be a note only (an interval, a
  piece outside the repertoire). A work may appear several times.
- In `edit_event`, omit an attribute to keep it and give an empty value to
  clear it; `clear_end` removes the end. A given `programme` **replaces the
  whole programme**: send the complete list.
- `set_programme_hidden` applies to concerts only. Members of the choir
  always see the programme; only the public does not.
- `list_events` without bounds lists the coming events over the default
  period (92 days unless configured). A period may not exceed the configured
  maximum (366 days by default): split longer requests.
- Deleting a work keeps its title in the programmes, without a link.
- `delete_event` requests confirmation. If the host opens the **Deletion**
  view, ask the user to review the event and choose **Delete** or
  **Cancel**.

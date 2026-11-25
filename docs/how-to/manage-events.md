<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Manage the events of a choir

In personal mode, ask the assistant to manage the concerts and rehearsals of
a choir. It uses the event tools described in the
[architecture](../architecture.md#event-tools-toolsevents); the
`manage-events` skill of the plugin guides it.

Who may see an event depends on its kind
([ADR 0031](../decisions/0031-model-choir-events-with-kind-based-visibility.md)):

| Kind | Visible to |
|---|---|
| Concert | Everyone, including the public. The public never sees the notes, nor the programme when it is hidden. |
| Rehearsal | The members of the choir. |
| Lesson | Its participants and the managers. Lessons come with choir members (#31). |

In personal mode you are the only user and see every event. The visibility
rules apply once events are shared.

## Add a concert with its programme

1. Make sure the works are in the repertoire (see the `manage-works` skill).
2. Ask, for example: "Add a concert *Christmas concert* on 20 December at
   20:30 at the cathedral, with *Ave Maria*, an interval, then *Gloria*."
3. The assistant calls `create_event` with the start in your time zone and
   the programme in order. A programme entry can be a work, a note, or both.

## Change an event or its programme

Ask for the change ("move the rehearsal to 19:00", "add *Ave Verum* at the
end of the programme"). The assistant calls `edit_event`; when the programme
changes, it sends the complete new programme. The kind of an event cannot
change: delete the event and create a new one.

## Hide a concert programme from the public

Ask "hide the programme of the Christmas concert". The assistant calls
`set_programme_hidden(event_id, true)`. Members of the choir still see it;
ask to show it again with `hidden` set to false.

## List the events of a period

Ask "what are our next events?" or "list the events of 2027". Without dates,
`list_events` covers the next 92 days; one listing covers at most 366 days.
Both values are settings: `MBC_EVENTS__DEFAULT_PERIOD_DAYS` and
`MBC_EVENTS__MAXIMUM_PERIOD_DAYS` (see the
[configuration reference](../configuration.md)).

## Delete an event

Ask to delete it. The assistant calls `delete_event`, which asks you to
confirm, or opens the **Deletion** view with its kind, start, choir and
number of programme entries. Deleting a work keeps its title in the
programmes that included it; deleting a choir deletes its events.

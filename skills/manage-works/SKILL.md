---
name: manage-works
description: Use when a my-beautiful-choir user wants to add a work (a piece) to a choir's repertoire, or change its title, composer, arranger, voicing, sung languages or notes, show or search the repertoire, open a work, or delete a work, in personal mode.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Manage the works of a repertoire

Works are managed with the tools of the my-beautiful-choir MCP server, in
personal mode.

## Tools

| Task | Tool |
|---|---|
| Add a work | `add_work(choir?, title, composer?, arranger?, voicing?, sung_languages?, notes?)` |
| Search a choir's repertoire | `show_repertoire(choir?, search?, page?, page_size?)` |
| Find scores and work IDs without opening a view | `list_scores(work_id?, work_title?, work_reference?, choir?)` |
| Show a work and its scores | `show_work(work_id)` |
| Change a work | `edit_work(work_id, ...)` |
| Delete a work and its scores | `delete_work(work_id)` |

## Rules to follow

- Only the title is required. Fill in only what the user gave; **never
  invent** a composer, an arranger or a voicing.
- Without `choir`, the work goes to the default choir: tell the user which
  one. If no choir exists, use the `manage-choirs` skill first.
- Sung languages are BCP 47 codes (`la` for Latin, `fr`, `en`, `de`...).
- In `edit_work`, omit an attribute to keep it; give an empty value to
  clear it. `sung_languages` replaces the whole list.
- A work is named by its id, given when it is added.
- Two works may have the same title (for example two arrangements).
- For score lookup, use `list_scores` with a work id, a title or a complete
  reference in the title. If several works match, ask which work the user
  means. Use `show_work` and `show_repertoire` when the user asks to show
  the corresponding view.
- `show_repertoire` returns one repertoire page, 10 works by default,
  ordered by title. Give `page_size` (up to 100) when the user asks for
  more works at once, and `page` to move on; the result says the page
  count and the number of matching works.
- `delete_work` requests confirmation. If the host opens the **Deletion**
  view, ask the user to review the work and its scores and choose
  **Delete** or **Cancel**. If the deletion preview changes, review it
  again before confirming.

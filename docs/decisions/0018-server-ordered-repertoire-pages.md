<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 18. Server-ordered repertoire pages

- Status: accepted
- Date: 2026-11-23
- Issue: #13
- Supersedes, for the works of the Repertoire view only: the sorting part
  of [ADR 0007](0007-mcp-apps-user-interface-stack.md) ("`Intl` for
  sorting")

## Context

`show_repertoire` returned every work of a choir and the view sorted them
with `Intl.Collator` in the host language. A large repertoire made the
view long and filled the model context with every work. Splitting the
works into pages requires a stable order before slicing, so the order can
no longer be decided by the view alone.

## Decision

Page the works on the server. `show_repertoire` accepts `page` (from 1)
and `page_size` (1 to 100, 10 by default) and returns one repertoire page
with the page number, the page size, the page count and the number of
matching works. A page past the last one returns the last one.

The SQL query orders the works on the normalized search columns
(`title_search`, then `composer_search` with no composer first, then
`id`), and applies `OFFSET` and `LIMIT`. The count and the page are read
in one snapshot. The view keeps the server order.

## Alternatives considered

- **Page in the view only**: keeps the exact language-aware order of
  `Intl.Collator`, but the model still receives every work. Rejected.
- **Language-aware ordering on the server with PyICU**: exact order for
  every language, but a native dependency to build on every platform, and
  the server would need the user's language. Rejected.

## Consequences

- The order ignores case and accents but follows code points, not the
  rules of each language (for example the Danish `ø` or the Spanish `ch`).
- The assistant can ask for a larger page or move between pages.
- Choir names are still sorted by the view with `Intl.Collator`.

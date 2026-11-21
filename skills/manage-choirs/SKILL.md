---
name: manage-choirs
description: Use when a my-beautiful-choir user wants to create, rename or list their choirs, or to choose the default choir (the one used when a request names none), in personal mode.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Manage choirs in my-beautiful-choir

Choirs are managed with the tools of the my-beautiful-choir MCP server, in
personal mode. Web mode does not offer them yet (they need accounts).

## Tools

| Task | Tool |
|---|---|
| See the choirs and the default choir | `list_choirs` |
| Create a choir | `create_choir(name)` |
| Rename a choir | `rename_choir(choir, new_name)` |
| Choose the default choir | `set_default_choir(choir)` |

## Rules to follow

- **Never invent a choir name**: ask the user for it.
- A choir name is unique, ignoring case, and has at most 100 characters.
- The first choir created becomes the **default choir**: tools taking an
  optional `choir` use it when the user names none. Tell the user which
  choir is used.
- When a tool answers that no choir exists yet, ask the user for the name
  of their first choir, then create it.
- Choirs are named by their name in every tool; use `list_choirs` to find
  the exact name.

## If a tool is missing

If these tools are not available, my-beautiful-choir may run in web mode,
or be an older version: see the `install` and `troubleshoot` skills.

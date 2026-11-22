---
name: uninstall
description: Use when a my-beautiful-choir user wants to remove the MCP server or its plugin, or remove the personal-mode database and score files from their computer.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Uninstall my-beautiful-choir

1. Ask which client and mode are affected. In personal mode, offer to
   preserve the data using `backup-and-restore`.
2. Stop the server and remove its registration from the client. Ask
   before editing client configuration and never read an environment
   configuration or credential file.
3. If requested, uninstall the plugin using the client's plugin manager.
   In web mode, stop the Compose service with the documented command.
4. The personal data directory is separate from the application checkout.
   State the exact path and its contents before asking the user to
   confirm any deletion. Delete personal data or the checkout only if
   the user explicitly confirms that specific path.

---
name: upgrade
description: Use when a my-beautiful-choir user wants to update a personal-mode installation, rebuild its views, or restore the previous version and data after an unsuccessful upgrade.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Upgrade my-beautiful-choir

1. Ask which version the user wants. Check the release notes or the
   repository changelog for migration requirements.
2. Stop the MCP client. Use the `backup-and-restore` skill before
   upgrading, and record the installed Git revision.
3. In a Git checkout, update to the requested revision following the
   repository's instructions. Preserve local edits. Run `uv sync --frozen`
   and `uv run --frozen nox -s ui` from the root.
4. Restart the client. The personal-mode server applies migrations during
   startup. Check the About view, the repertoire and a score. Use
   `troubleshoot` if startup fails.
5. To roll back, stop the client, return to the old revision, rebuild its
   views and restore the pre-upgrade backup when the database has been
   migrated. Ask for confirmation before restoring data.

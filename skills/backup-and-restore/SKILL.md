---
name: backup-and-restore
description: Use when a personal-mode my-beautiful-choir user wants to back up, move, export or restore their data directory, including both the repertoire database and stored scores.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Back up and restore personal data

Follow `docs/how-to/back-up-and-restore-personal-data.md` in the repository.
Ask if the user configured a custom `MBC_DATA_DIR`; use the documented
platform default otherwise. Never open local environment configuration
or credential files. Stop the personal-mode server before copying the
whole directory. Ask for explicit confirmation before replacing any
existing directory, and retain a separate copy of the current data.

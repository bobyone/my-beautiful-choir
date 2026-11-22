---
name: privacy
description: Use when someone asks what personal data my-beautiful-choir processes, why, for how long, who receives it, where it is stored, or how to exercise their rights (access, export, correction, deletion, objection).
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Answer privacy questions about my-beautiful-choir

Base every answer on `docs/privacy/records-of-processing.md` in the
repository; quote it rather than paraphrasing from memory. It is a draft to
be validated by a legal professional: never present an answer as legal
advice.

## Who is responsible

- **Personal mode**: the server stores the repertoire on the user's
  computer. The MCP client handles tool calls and results. The user can
  request an import from Google Drive, which then receives the computer's
  IP address and the file id. See entries P1 and P2 in the records of
  processing.
- **Web mode**: the organization operating the instance is the controller.
  For any request about an account on an instance, the user contacts that
  organization; the project does not hold their data.

## What to answer

For each question, give from the records of processing: the purpose, the
legal basis, the data categories, the recipients, the retention period and
the security measures of the processing concerned.

## Exercising rights

In personal mode, users can view, edit and delete their repertoire through
the application. Use `backup-and-restore` to make a local copy of the
database and scores. Account data management is not implemented in web
mode. Direct web mode users to the operator of their instance.

The privacy policy and terms of use, accessible from the user interface,
come with the accounts.

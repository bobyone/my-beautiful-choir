---
name: report-issue
description: Use when a my-beautiful-choir user wants to report a bug, propose a feature or improvement, or contribute code to the project. Gathers the needed information, then opens the GitHub issue after confirmation, or guides the user to fork and clone the repository.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Report an issue or contribute to my-beautiful-choir

## 1. Identify the request

Ask the user whether they want to:

- report a bug;
- propose a feature or an improvement;
- contribute code themselves.

If the request concerns a **security vulnerability**, do not open a public
issue: point the user to
<https://github.com/bobyone/my-beautiful-choir/security/advisories/new> and
stop here.

## 2. Gather the information

For a bug, collect:

- the version of my-beautiful-choir and the mode (web mode or personal
  mode);
- the MCP client, its version and the operating system;
- the steps to reproduce, the expected and the actual behaviour;
- relevant log excerpts.

Before including any log excerpt, remove secrets (tokens, passwords, keys)
and personal data (names, e-mail addresses). Never read environment
configuration files such as `.env`.

For a feature, collect the need, the acceptance criteria, what is out of
scope and the modes concerned. Use the terms of the project glossary
(<https://github.com/bobyone/my-beautiful-choir/blob/main/docs/glossary.md>).

## 3. Open the issue

1. Show the user the full issue title and body, in English, following the
   matching template (`bug_report.yml` or `feature_request.yml`).
2. **Ask for explicit confirmation** before opening it.
3. If the GitHub CLI is available and authenticated (`gh auth status`),
   open it:

   ```sh
   gh issue create --repo bobyone/my-beautiful-choir --label bug --title "<title>" --body-file <file>
   ```

   Use the `enhancement` label for a feature. Otherwise, give the user the
   prepared text and the link
   <https://github.com/bobyone/my-beautiful-choir/issues/new/choose>.

## 4. Contribute code

When the user wants to implement the change:

1. Make sure an issue exists and that a maintainer agreed with the need.
2. Guide them to fork and clone the repository:

   ```sh
   gh repo fork bobyone/my-beautiful-choir --clone
   ```

3. From the clone, the repository's own `contribute` development skill and
   `CONTRIBUTING.md` take over: do not repeat their content here.

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 8. Internationalization

- Status: accepted
- Date: 2026-11-21
- Issue: #1

## Context

The UI is shown to choristers across Europe. Part of the server output,
however, is read by the language model rather than by the user: tool
descriptions, input schemas and text results.

## Decision

- Source language is English.
- Target languages are the national official languages of European
  states (the 24 EU official languages, plus `sq`, `hy`, `az`, `be`, `bs`,
  `ca`, `ka`, `is`, `lb`, `mk`, `cnr`, `nb`, `nn`, `rm`, `ru`, `sr-Cyrl`,
  `sr-Latn`, `tr`, `uk`).
- Translated: the MCP Apps UI, the OAuth login page, e-mails sent to users,
  and user-facing legal texts.
- Kept in English: tool names and descriptions, input schemas and text
  results meant for the model, logs and internal exceptions. The model
  rephrases results in the user's language.
- A language not supported by a library falls back to the closest one
  (`cnr` falls back to `sr-Latn`).
- Adding a language only requires adding translation files.
- Dates are stored in UTC and displayed in the user's time zone.
- Machine-produced translations are marked as needing review by a native
  speaker.

## Alternatives

- Translating tool descriptions and results: the model handles English best
  and translates for the user anyway; translating would multiply catalogue
  size for no user benefit.

## Consequences

- CI checks that every key exists in every language, that no key is unused
  and that placeholders match across languages, for both the Python
  catalogues and the UI catalogues.

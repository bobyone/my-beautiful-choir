<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# How to add a language or fix a translation

The user interface is translated with [i18next](https://www.i18next.com/)
and the ICU message format. Each language has one catalogue,
`ui/locales/<code>.json`, where `<code>` is a BCP 47 tag (`fr`, `pt`,
`sr-Latn`…). English (`en.json`) is the source language.

No code change is needed: the views load every catalogue found in
`ui/locales/`.

## Fix a translation

1. Edit the message in `ui/locales/<code>.json`. Keep the parameters in
   braces unchanged (`{name}`), and use the typographic apostrophe `’`: a
   straight apostrophe has a special meaning in ICU messages.
2. If you are a native speaker and reviewed the whole catalogue, remove its
   code from `ui/i18n/review.json`.
3. Run the checks: `uv run nox -s ui_check`.

## Add a language

1. Copy `ui/locales/en.json` to `ui/locales/<code>.json` and translate
   every message. Keep the keys and the parameters unchanged; plural forms
   use the ICU `plural` syntax with the categories of the language.
2. Unless you are a native speaker, add the code to `ui/i18n/review.json`.
3. If the language is close to an existing one that should be used for its
   regional variants or related tags, declare it in `ui/i18n/fallbacks.json`
   (for example `"cnr": "sr-Latn"`: Montenegrin uses the Serbian Latin
   catalogue until it has its own).
4. Translate the glossary labels (`glossary.*` keys) consistently with
   [the glossary](../glossary.md).
5. Run the checks: `uv run nox -s ui_check`. They fail when a key is
   missing or unknown, when a message is not valid ICU, when parameters
   differ from English, or when a key is unused in the code.
6. Build the views (`uv run nox -s ui`) and check the result in an MCP
   client set to that language.

## How the language is chosen

The view follows the language of the MCP host. It tries, in order: the full
tag (`sr-Latn-RS`), the language and script (`sr-Latn`), the language
(`sr`), each time with its fallback from `ui/i18n/fallbacks.json`; then
English.

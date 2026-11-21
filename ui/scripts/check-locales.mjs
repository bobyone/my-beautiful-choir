// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

/**
 * Checks the translation catalogues against the English one:
 * - every catalogue has exactly the same keys;
 * - every message is valid ICU and uses the same parameters;
 * - review and fallback lists only name existing catalogues;
 * - every glossary term (docs/glossary.md) has its key.
 * Unused keys are detected by `i18next-cli extract --ci`.
 * Exits with code 1 and lists every problem when a check fails.
 */

import { readFileSync, readdirSync } from "node:fs";

import { IntlMessageFormat } from "intl-messageformat";

const SOURCE_LANGUAGE = "en";
const root = new URL("../", import.meta.url);
const readJson = (path) => JSON.parse(readFileSync(new URL(path, root), "utf-8"));

function flatten(object, prefix = "") {
  return Object.entries(object).flatMap(([key, value]) =>
    typeof value === "object" && value !== null
      ? flatten(value, `${prefix}${key}.`)
      : [[`${prefix}${key}`, value]],
  );
}

function argumentsOf(nodes, found = new Set()) {
  for (const node of nodes) {
    if ("value" in node && node.type !== 0 && node.type !== 7) {
      found.add(node.value);
    }
    for (const option of Object.values(node.options ?? {})) {
      argumentsOf(option.value, found);
    }
    argumentsOf(node.children ?? [], found);
  }
  return found;
}

const problems = [];
const catalogues = Object.fromEntries(
  readdirSync(new URL("locales/", root))
    .filter((file) => file.endsWith(".json"))
    .map((file) => [file.replace(/\.json$/, ""), new Map(flatten(readJson(`locales/${file}`)))]),
);
const source = catalogues[SOURCE_LANGUAGE];
if (source === undefined) {
  problems.push(`locales/${SOURCE_LANGUAGE}.json is missing`);
} else {
  for (const [language, catalogue] of Object.entries(catalogues)) {
    for (const key of source.keys()) {
      if (!catalogue.has(key)) problems.push(`${language}: missing key ${key}`);
    }
    for (const [key, message] of catalogue) {
      if (!source.has(key)) {
        problems.push(`${language}: unknown key ${key}`);
        continue;
      }
      if (typeof message !== "string") {
        problems.push(`${language}: ${key} is not a text`);
        continue;
      }
      let parameters;
      try {
        parameters = argumentsOf(new IntlMessageFormat(message, language).getAst());
      } catch (error) {
        problems.push(`${language}: ${key} is not valid ICU (${error.message})`);
        continue;
      }
      const expected = argumentsOf(new IntlMessageFormat(source.get(key), "en").getAst());
      const same =
        parameters.size === expected.size && [...parameters].every((name) => expected.has(name));
      if (!same) {
        problems.push(
          `${language}: ${key} uses {${[...parameters].join(", ")}}, expected {${[...expected].join(", ")}}`,
        );
      }
    }
  }
}

for (const language of readJson("i18n/review.json").toReview) {
  if (!(language in catalogues)) problems.push(`i18n/review.json: no catalogue for ${language}`);
}
for (const [language, fallback] of Object.entries(readJson("i18n/fallbacks.json"))) {
  if (language in catalogues) problems.push(`i18n/fallbacks.json: ${language} has a catalogue`);
  if (!(fallback in catalogues)) problems.push(`i18n/fallbacks.json: no catalogue for ${fallback}`);
}

const glossary = readFileSync(new URL("../docs/glossary.md", root), "utf-8");
for (const [, key] of glossary.matchAll(/`(glossary\.[A-Za-z]+)`/g)) {
  if (source !== undefined && !source.has(key)) {
    problems.push(`docs/glossary.md: ${key} is missing from locales/${SOURCE_LANGUAGE}.json`);
  }
}

if (problems.length > 0) {
  console.error(`Translation catalogues: ${problems.length} problem(s)`);
  for (const problem of problems) console.error(`  - ${problem}`);
  process.exit(1);
}
console.log(`Translation catalogues: ${Object.keys(catalogues).length} languages checked.`);

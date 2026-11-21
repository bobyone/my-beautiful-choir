// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { readdirSync } from "node:fs";

import { defineConfig } from "i18next-cli";

// Languages are the catalogues present in locales/: adding a language only requires its file.
const locales = readdirSync(new URL("./locales/", import.meta.url))
  .filter((file) => file.endsWith(".json"))
  .map((file) => file.replace(/\.json$/, ""))
  .sort();

export default defineConfig({
  locales,
  extract: {
    input: ["src/**/*.{ts,tsx}"],
    ignore: ["src/**/*.test.{ts,tsx}", "src/test/**"],
    output: "locales/{{language}}.json",
    primaryLanguage: "en",
    defaultNS: false,
    removeUnusedKeys: true,
    sort: true,
    indentation: 2,
  },
});

// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import js from "@eslint/js";
import tseslint from "typescript-eslint";

// Configuration files and Node scripts, outside the TypeScript project.
const toolingFiles = ["*.js", "i18next.config.ts", "scripts/*.mjs"];

export default tseslint.config(
  { ignores: ["dist", "coverage", "node_modules"] },
  js.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: { allowDefaultProject: toolingFiles },
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    files: toolingFiles,
    ...tseslint.configs.disableTypeChecked,
    languageOptions: {
      globals: { process: "readonly", console: "readonly", URL: "readonly" },
    },
  },
);

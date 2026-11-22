// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { readFile, readdir, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";
import { fileURLToPath } from "node:url";

import { build } from "vite";

const uiDirectory = fileURLToPath(new URL("../", import.meta.url));
const viewsDirectory = join(uiDirectory, "views");
const outputDirectory = join(uiDirectory, "dist");
const views = (await readdir(viewsDirectory)).filter((name) => name.endsWith(".html")).sort();
if (views.length === 0) {
  throw new Error("No MCP Apps views were found.");
}

// Each entry needs an independent build to inline all of its scripts and styles.
const licenses = new Map();
for (const [index, view] of views.entries()) {
  const licenseFile = `.vite/${basename(view, ".html")}.licenses.json`;
  await build({
    root: uiDirectory,
    build: {
      emptyOutDir: index === 0,
      license: { fileName: licenseFile },
      rolldownOptions: { input: join(viewsDirectory, view) },
    },
  });
  const entries = JSON.parse(await readFile(join(outputDirectory, licenseFile), "utf8"));
  for (const entry of entries) {
    licenses.set(`${entry.name}@${entry.version}`, entry);
  }
}

const sections = [...licenses.keys()].sort().map((key) => {
  const { name, version, identifier, text } = licenses.get(key);
  const heading = `## ${name} - ${version}${identifier ? ` (${identifier})` : ""}`;
  return text ? `${heading}\n\n${text}\n` : `${heading}\n`;
});
await writeFile(
  join(outputDirectory, ".vite", "license.md"),
  ["# Licenses\n", ...sections].join("\n"),
  "utf8",
);

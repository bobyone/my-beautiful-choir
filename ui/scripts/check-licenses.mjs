// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

/**
 * Checks that every production dependency (bundled into the views, hence
 * distributed with my-beautiful-choir) has a licence compatible with
 * GPL-2.0-or-later. Exits with code 1 and lists the others.
 */

import { execFileSync } from "node:child_process";

const ALLOWED = new Set([
  "0BSD",
  "Apache-2.0",
  "BSD-2-Clause",
  "BSD-3-Clause",
  "CC0-1.0",
  "ISC",
  "MIT",
  "GPL-2.0-or-later",
]);

// Run through `npm run licenses`: npm gives the path of its own CLI.
const npmCli = process.env["npm_execpath"];
if (npmCli === undefined) {
  console.error("Run this script with: npm run licenses");
  process.exit(2);
}
const packages = JSON.parse(
  execFileSync(process.execPath, [npmCli, "query", ".prod"], { encoding: "utf-8" }),
);

const rejected = packages
  .filter((pkg) => !ALLOWED.has(typeof pkg.license === "string" ? pkg.license : ""))
  .map((pkg) => `${pkg.name}@${pkg.version}: ${JSON.stringify(pkg.license ?? null)}`);

if (rejected.length > 0) {
  console.error("Production dependencies with a licence not allowed:");
  for (const entry of rejected) console.error(`  - ${entry}`);
  process.exit(1);
}
console.log(`Licences: ${packages.length} production packages checked.`);

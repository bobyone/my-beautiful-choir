// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import axe from "axe-core";

/**
 * Accessibility violations (WCAG 2.2 A and AA rules) found by axe-core in an element.
 * Colour contrast is not checked: jsdom does not compute styles.
 */
export async function accessibilityViolations(element: Element): Promise<string[]> {
  const results = await axe.run(element, {
    runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
    rules: { "color-contrast": { enabled: false } },
  });
  return results.violations.map((violation) => `${violation.id}: ${violation.help}`);
}

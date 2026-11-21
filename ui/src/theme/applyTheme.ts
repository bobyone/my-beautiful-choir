// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

export type Theme = "light" | "dark";

/** Applies the host theme to Bootstrap (`data-bs-theme`); light when the host gives none. */
export function applyTheme(
  theme: Theme | undefined,
  root: HTMLElement = document.documentElement,
): void {
  root.dataset["bsTheme"] = theme ?? "light";
}

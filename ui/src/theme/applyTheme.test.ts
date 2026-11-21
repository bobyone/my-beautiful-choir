// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { describe, expect, it } from "vitest";

import { applyTheme } from "./applyTheme";

describe("applyTheme", () => {
  it("applies the host theme to Bootstrap", () => {
    const root = document.createElement("html");
    applyTheme("dark", root);
    expect(root.dataset["bsTheme"]).toBe("dark");
  });

  it("defaults to the light theme", () => {
    applyTheme(undefined);
    expect(document.documentElement.dataset["bsTheme"]).toBe("light");
  });
});

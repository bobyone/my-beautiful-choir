// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { i18n as I18n } from "i18next";
import { useEffect } from "react";

import { AVAILABLE_LANGUAGES, FALLBACKS } from "../i18n/catalogues";
import { resolveLanguage } from "../i18n/resolveLanguage";
import { applyTheme } from "../theme/applyTheme";
import type { HostState } from "./useHost";

/** Follows the language and the theme of the host, as every view does. */
export function useHostLanguageAndTheme(host: HostState, i18n: I18n): void {
  const language = resolveLanguage(host.hostContext?.locale, AVAILABLE_LANGUAGES, FALLBACKS);
  const theme = host.hostContext?.theme;

  useEffect(() => {
    void i18n.changeLanguage(language);
    document.documentElement.lang = language;
  }, [i18n, language]);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);
}

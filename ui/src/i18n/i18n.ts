// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { createInstance, type i18n as I18n } from "i18next";
import ICU from "i18next-icu";
import { initReactI18next } from "react-i18next";

import { DEFAULT_LANGUAGE } from "./resolveLanguage";
import { RESOURCES } from "./catalogues";

/**
 * Creates the translation instance: ICU message format (named parameters,
 * plural rules of each language), English as fallback.
 */
export async function createI18n(language: string = DEFAULT_LANGUAGE): Promise<I18n> {
  const instance = createInstance();
  await instance
    .use(ICU)
    .use(initReactI18next)
    .init({
      resources: RESOURCES,
      lng: language,
      fallbackLng: DEFAULT_LANGUAGE,
      interpolation: { escapeValue: false },
      returnNull: false,
    });
  return instance;
}

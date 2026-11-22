// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { i18n as I18n } from "i18next";
import { I18nextProvider } from "react-i18next";

import { useHost } from "../../host/useHost";
import { useHostLanguageAndTheme } from "../../host/useHostLanguageAndTheme";
import { parseAboutInfo } from "./aboutInfo";
import { AboutView, type AboutState } from "./AboutView";

export const VIEW_NAME = "my-beautiful-choir-about";
export const VIEW_VERSION = "1.0.0";

/** Connects the "About" view to the host: language, theme and tool result. */
export function AboutApp({ i18n }: { i18n: I18n }) {
  const host = useHost(VIEW_NAME, VIEW_VERSION);
  useHostLanguageAndTheme(host, i18n);

  return (
    <I18nextProvider i18n={i18n}>
      <AboutView state={stateOf(host)} />
    </I18nextProvider>
  );
}

function stateOf(host: ReturnType<typeof useHost>): AboutState {
  if (host.connectionFailed) {
    return { kind: "connection-error" };
  }
  if (host.toolResult === undefined) {
    return { kind: "loading" };
  }
  const info = parseAboutInfo(host.toolResult);
  return info === undefined ? { kind: "error" } : { kind: "ready", info };
}

// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-FileContributor: bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { i18n as I18n } from "i18next";
import { I18nextProvider } from "react-i18next";

import { useHost } from "../../host/useHost";
import { useHostLanguageAndTheme } from "../../host/useHostLanguageAndTheme";
import { ViewStatus } from "../ViewStatus";
import { parseFinalisation } from "./finalisationInfo";
import { parseWorkResult } from "./workInfo";
import { WorkPanel } from "./WorkPanel";

export function WorkApp({ i18n }: { i18n: I18n }) {
  const host = useHost("my-beautiful-choir-work", "1.0.0");
  useHostLanguageAndTheme(host, i18n);
  const data = host.toolResult && parseWorkResult(host.toolResult);
  const initialFinalisation = host.toolResult && parseFinalisation(host.toolResult);
  return (
    <I18nextProvider i18n={i18n}>
      {host.connectionFailed ? (
        <ViewStatus kind="connection-error" />
      ) : host.toolResult === undefined ? (
        <ViewStatus kind="loading" />
      ) : data === undefined ? (
        <ViewStatus kind="error" />
      ) : (
        <main>
          <WorkPanel
            key={initialFinalisation?.token ?? data.work.id}
            data={data}
            initialFinalisation={initialFinalisation}
            timeZone={host.hostContext?.timeZone}
            callTool={host.callTool}
            downloadFile={host.canDownload ? host.downloadFile : undefined}
          />
        </main>
      )}
    </I18nextProvider>
  );
}

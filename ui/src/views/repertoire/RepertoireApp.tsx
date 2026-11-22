// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { i18n as I18n } from "i18next";
import { I18nextProvider } from "react-i18next";

import { useHost } from "../../host/useHost";
import { useHostLanguageAndTheme } from "../../host/useHostLanguageAndTheme";
import { ViewStatus } from "../ViewStatus";
import { parseRepertoire } from "./repertoireInfo";
import { RepertoirePanel } from "./RepertoirePanel";

export function RepertoireApp({ i18n }: { i18n: I18n }) {
  const host = useHost("my-beautiful-choir-repertoire", "1.0.0");
  useHostLanguageAndTheme(host, i18n);
  const data = host.toolResult && parseRepertoire(host.toolResult);
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
          <RepertoirePanel data={data} callTool={host.callTool} />
        </main>
      )}
    </I18nextProvider>
  );
}

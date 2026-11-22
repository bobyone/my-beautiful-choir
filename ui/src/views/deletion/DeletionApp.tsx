// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { i18n as I18n } from "i18next";
import { useState } from "react";
import { I18nextProvider } from "react-i18next";

import { useHost, type HostState } from "../../host/useHost";
import { useHostLanguageAndTheme } from "../../host/useHostLanguageAndTheme";
import { parseDeletionInfo } from "./deletionInfo";
import { DeletionView, type DeletionState } from "./DeletionView";

export const VIEW_NAME = "my-beautiful-choir-deletion";
export const VIEW_VERSION = "1.0.0";
export const CONFIRM_TOOL = "confirm_deletion";

/** What the user did in the view, for a deletion awaiting confirmation. */
type Progress = "waiting" | "deleting" | "deleted" | "cancelled" | "failed";

/**
 * Connects the "Deletion" view to the host. A pending deletion is confirmed
 * with the app-only `confirm_deletion` tool, only when the user presses "Delete".
 */
export function DeletionApp({ i18n }: { i18n: I18n }) {
  const host = useHost(VIEW_NAME, VIEW_VERSION);
  useHostLanguageAndTheme(host, i18n);
  const [progress, setProgress] = useState<Progress>("waiting");
  const state = stateOf(host, progress);
  const info = host.toolResult === undefined ? undefined : parseDeletionInfo(host.toolResult);

  const onDelete = () => {
    if (info?.status !== "pending" || progress !== "waiting") {
      return;
    }
    setProgress("deleting");
    host
      .callTool(CONFIRM_TOOL, { token: info.token })
      .then((result) => {
        setProgress(parseDeletionInfo(result)?.status === "deleted" ? "deleted" : "failed");
      })
      .catch(() => {
        setProgress("failed");
      });
  };

  return (
    <I18nextProvider i18n={i18n}>
      <DeletionView
        state={state}
        onDelete={onDelete}
        onCancel={() => {
          setProgress("cancelled");
        }}
      />
    </I18nextProvider>
  );
}

function stateOf(host: HostState, progress: Progress): DeletionState {
  if (host.connectionFailed) {
    return { kind: "connection-error" };
  }
  if (host.toolResult === undefined) {
    return { kind: "loading" };
  }
  const info = parseDeletionInfo(host.toolResult);
  if (info === undefined) {
    return { kind: "error" };
  }
  const { deletion } = info;
  if (info.status === "deleted") {
    return { kind: "deleted", deletion };
  }
  if (info.status === "refused") {
    return { kind: "nothing-deleted", deletion };
  }
  switch (progress) {
    case "waiting":
      return { kind: "pending", deletion };
    case "cancelled":
      return { kind: "nothing-deleted", deletion };
    default:
      return { kind: progress, deletion };
  }
}

// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type {
  App,
  McpUiDownloadFileRequest,
  McpUiHostContext,
  McpUiToolResultNotification,
} from "@modelcontextprotocol/ext-apps";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";
import { useCallback, useState } from "react";

export type ToolResult = McpUiToolResultNotification["params"];

/** Result of a tool called by the view. */
export type CalledToolResult = Awaited<ReturnType<App["callServerTool"]>>;

/** A file the view asks the host to save: an embedded resource or a resource link. */
export type DownloadableFile = McpUiDownloadFileRequest["params"]["contents"][number];

/** Asks the host to save a file; resolves to "cancelled" when the user or the host refused. */
export type DownloadFile = (file: DownloadableFile) => Promise<"done" | "cancelled">;

export interface HostState {
  /** True once the view is connected to the host. */
  connected: boolean;
  /** True when the connection to the host failed. */
  connectionFailed: boolean;
  /** Current host context (language, time zone, theme…), merged with its changes. */
  hostContext: McpUiHostContext | undefined;
  /** Result of the tool displayed by the view, once received. */
  toolResult: ToolResult | undefined;
  /** Calls a tool of the server, such as an app-only tool; rejects when not connected. */
  callTool: (name: string, args: Record<string, unknown>) => Promise<CalledToolResult>;
  /** True when the host advertises that it can save a file for the view. */
  canDownload: boolean;
  /** Asks the host to save a file; rejects when not connected or when the request fails. */
  downloadFile: DownloadFile;
}

/**
 * Connects the view to the MCP host: receives the tool result and the host
 * context, applies the host styles (CSS variables, color scheme, fonts), and
 * lets the view call the tools of the server.
 */
export function useHost(viewName: string, version: string): HostState {
  const [hostContext, setHostContext] = useState<McpUiHostContext | undefined>(undefined);
  const [toolResult, setToolResult] = useState<ToolResult | undefined>(undefined);

  const { app, isConnected, error } = useApp({
    appInfo: { name: viewName, version },
    capabilities: {},
    onAppCreated: (created) => {
      created.addEventListener("toolresult", (result) => {
        setToolResult(result);
      });
      // A change carries only the modified fields; the SDK merges it into the
      // full context before notifying.
      created.addEventListener("hostcontextchanged", () => {
        setHostContext(created.getHostContext());
      });
    },
  });

  const initialContext = app?.getHostContext();
  useHostStyles(app, initialContext);

  const callTool = useCallback(
    async (name: string, args: Record<string, unknown>): Promise<CalledToolResult> => {
      if (app === null) {
        throw new Error("The view is not connected to the host.");
      }
      return app.callServerTool({ name, arguments: args });
    },
    [app],
  );

  const downloadFile = useCallback(
    async (file: DownloadableFile): Promise<"done" | "cancelled"> => {
      if (app === null) {
        throw new Error("The view is not connected to the host.");
      }
      const reply = await app.downloadFile({ contents: [file] });
      return reply.isError === true ? "cancelled" : "done";
    },
    [app],
  );

  return {
    connected: isConnected,
    connectionFailed: error !== null,
    hostContext: hostContext ?? initialContext,
    toolResult,
    callTool,
    canDownload: isConnected && app?.getHostCapabilities()?.downloadFile !== undefined,
    downloadFile,
  };
}

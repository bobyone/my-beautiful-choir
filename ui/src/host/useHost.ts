// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { McpUiHostContext, McpUiToolResultNotification } from "@modelcontextprotocol/ext-apps";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";
import { useState } from "react";

export type ToolResult = McpUiToolResultNotification["params"];

export interface HostState {
  /** True once the view is connected to the host. */
  connected: boolean;
  /** True when the connection to the host failed. */
  connectionFailed: boolean;
  /** Current host context (language, time zone, theme…), merged with its changes. */
  hostContext: McpUiHostContext | undefined;
  /** Result of the tool displayed by the view, once received. */
  toolResult: ToolResult | undefined;
}

/**
 * Connects the view to the MCP host: receives the tool result and the host
 * context, and applies the host styles (CSS variables, color scheme, fonts).
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

  return {
    connected: isConnected,
    connectionFailed: error !== null,
    hostContext: hostContext ?? initialContext,
    toolResult,
  };
}

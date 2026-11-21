// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { App, McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import type { UseAppOptions } from "@modelcontextprotocol/ext-apps/react";

import type { ToolResult } from "../host/useHost";

type Listener = (params: never) => void;

/**
 * Stands for the MCP host in tests: replaces `useApp` and lets the test push a
 * tool result or a host context change to the view.
 */
export class FakeHost {
  connected = true;
  error: Error | null = null;
  initialContext: McpUiHostContext | undefined;
  private readonly listeners = new Map<string, Listener[]>();
  private created = false;

  readonly app = {
    getHostContext: (): McpUiHostContext | undefined => this.initialContext,
    addEventListener: (event: string, handler: Listener): void => {
      this.listeners.set(event, [...(this.listeners.get(event) ?? []), handler]);
    },
  };

  useApp = (options: UseAppOptions) => {
    const app = this.app as unknown as App;
    if (!this.created) {
      this.created = true;
      options.onAppCreated?.(app);
    }
    return {
      app: this.connected ? app : null,
      isConnected: this.connected,
      error: this.error,
    };
  };

  sendToolResult(result: ToolResult): void {
    this.emit("toolresult", result);
  }

  changeHostContext(changes: McpUiHostContext): void {
    this.emit("hostcontextchanged", changes);
  }

  private emit(event: string, params: unknown): void {
    for (const listener of this.listeners.get(event) ?? []) {
      (listener as (value: unknown) => void)(params);
    }
  }
}

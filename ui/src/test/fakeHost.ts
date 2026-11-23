// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { App, McpUiHostCapabilities, McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import type { UseAppOptions } from "@modelcontextprotocol/ext-apps/react";

import type { CalledToolResult, DownloadableFile, ToolResult } from "../host/useHost";

export interface ToolCall {
  name: string;
  arguments?: Record<string, unknown>;
}

type Listener = (params: never) => void;

/**
 * Stands for the MCP host in tests: replaces `useApp` and lets the test push a
 * tool result or a host context change to the view.
 */
export class FakeHost {
  connected = true;
  error: Error | null = null;
  initialContext: McpUiHostContext | undefined;
  /** Tool calls made by the view, in order. */
  readonly toolCalls: ToolCall[] = [];
  /** Answers the tool calls of the view; rejects with ``toolCallError`` when set. */
  answerToolCall: (call: ToolCall) => CalledToolResult = () => ({ content: [] });
  toolCallError: Error | null = null;
  /** Capabilities the host advertises; `{ downloadFile: {} }` lets the view download. */
  capabilities: McpUiHostCapabilities = {};
  /** Files the view asked the host to save, in order. */
  readonly downloads: DownloadableFile[][] = [];
  /** Answer of the host to a download request; `isError` stands for a refusal. */
  downloadAnswer: { isError?: boolean } | Error = {};
  private readonly listeners = new Map<string, Listener[]>();
  private created = false;

  readonly app = {
    getHostContext: (): McpUiHostContext | undefined => this.initialContext,
    addEventListener: (event: string, handler: Listener): void => {
      this.listeners.set(event, [...(this.listeners.get(event) ?? []), handler]);
    },
    getHostCapabilities: (): McpUiHostCapabilities => this.capabilities,
    downloadFile: (params: { contents: DownloadableFile[] }): Promise<{ isError?: boolean }> => {
      this.downloads.push(params.contents);
      return this.downloadAnswer instanceof Error
        ? Promise.reject(this.downloadAnswer)
        : Promise.resolve(this.downloadAnswer);
    },
    callServerTool: (call: ToolCall): Promise<CalledToolResult> => {
      this.toolCalls.push(call);
      return this.toolCallError === null
        ? Promise.resolve(this.answerToolCall(call))
        : Promise.reject(this.toolCallError);
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

  /** Like the SDK, merges the changes into the context before notifying the view. */
  changeHostContext(changes: McpUiHostContext): void {
    this.initialContext = { ...this.initialContext, ...changes };
    this.emit("hostcontextchanged", changes);
  }

  private emit(event: string, params: unknown): void {
    for (const listener of this.listeners.get(event) ?? []) {
      (listener as (value: unknown) => void)(params);
    }
  }
}

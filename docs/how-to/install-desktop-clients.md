<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Install for Claude Desktop or ChatGPT desktop

From a clone of the repository, use Python 3.13 or later, uv, and Node.js
with npm. Choose the command for your local client.

| Client | Supported platforms | Command |
|---|---|---|
| Claude Desktop | Windows and macOS | `python scripts/install_claude_desktop.py` |
| ChatGPT desktop, in a local Codex session | Windows and macOS | `python scripts/install_chatgpt_desktop.py` |
| Local Codex CLI | Windows, macOS and Linux | `python scripts/install_chatgpt_desktop.py` |

Open Claude Desktop at least once to create its configuration directory.
For ChatGPT desktop or Codex, make the `codex` command available on PATH
and use the same local Codex profile as your client. The ChatGPT web
conversation uses a different setup.

If Node.js and npm are installed outside PATH, append
`--node-dir "path to the Node.js directory"` to the chosen command. The
installer syncs the locked Python environment, builds the interface and
checks the MCP connection with temporary data before registering the
server. The launcher points to this checkout, so reinstall after moving it.

Run the command again to refresh the build. An identical registration
is kept. If the existing entry points elsewhere, review the prompt before
replacing it. For an intentional non-interactive replacement, use
`--replace`. Other registrations are preserved.

Fully quit and reopen Claude Desktop, or restart the local Codex session.
Ask *"Show me information about my-beautiful-choir."* A successful
response identifies the application and personal mode.

To disconnect, remove only the `my-beautiful-choir` entry in Claude
Desktop's developer configuration, or run
`codex mcp remove my-beautiful-choir` for Codex. This disconnects the client
and leaves the repertoire and score files in the data directory.

See [startup troubleshooting](troubleshoot-startup.md) if the server
cannot start.

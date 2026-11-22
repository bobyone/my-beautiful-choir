---
name: install
description: Use when someone wants to install, set up or run my-beautiful-choir - in personal mode in their MCP client (Claude Desktop, VS Code...) or in web mode with Docker Compose - or to install this plugin and keep it up to date in Claude Code or Codex.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Install my-beautiful-choir

my-beautiful-choir is an MCP app. Ask the user which mode they want:

- **personal mode**: on their own computer, for themselves, started by their
  MCP client;
- **web mode**: a shared service for several choirs, run with Docker.

my-beautiful-choir is not published on PyPI yet: both modes run from a
clone of the repository. Follow `docs/quick-start.md` of the repository;
the steps below summarize it.

## Personal mode

For Claude Desktop or ChatGPT desktop with local Codex, use
`docs/how-to/install-desktop-clients.md`. Run the installation command
for the selected client from the clone. The installer builds the interface,
verifies personal mode with temporary data, and registers the server. Ask
before launching the installer against a user's live client settings.

For manual setup or another local MCP client, follow the steps below.

1. Check the prerequisites: `git --version`, `uv --version`,
   `node --version` (Node.js LTS, only to build the user interface).
   Point to <https://docs.astral.sh/uv/> or <https://nodejs.org/> if one
   is missing.
2. Clone and build:

   ```sh
   git clone https://github.com/bobyone/my-beautiful-choir.git
   cd my-beautiful-choir
   uv sync
   uv run nox -s ui
   ```

3. Declare the server in the MCP client. Show the user the configuration
   to add, with the absolute path of their clone, and **ask before editing
   any client configuration file**. For Claude Desktop:

   ```json
   {
     "mcpServers": {
       "my-beautiful-choir": {
         "command": "uv",
         "args": ["run", "--directory", "/path/to/my-beautiful-choir", "my-beautiful-choir"]
       }
     }
   }
   ```

4. Ask the user to restart the client, then to ask *"Show me information
   about my-beautiful-choir"*.

To use a custom data directory, set `MBC_DATA_DIR` in the MCP client's
server environment. The directory contains both the database and stored
scores. See `docs/configuration.md` and the `backup-and-restore` skill.

## Web mode

Web mode has no authentication yet: it must not be exposed publicly. Say
so to the user before going further.

1. Check Docker: `docker compose version`.
2. From the clone, optionally create the configuration from its example:
   `cp .env.example .env`, then adjust it with the user (see
   `docs/configuration.md`). Never read an existing `.env` file.
3. Start: `docker compose up --detach --build`.
4. Check: `http://localhost:9000/healthz` answers `{"status": "ready"}`.
5. The MCP endpoint is `http://localhost:9000/mcp` (Streamable HTTP).

## This plugin

### Codex

Follow the repository guide in `docs/how-to/install-the-plugin-in-codex.md`.
Add the catalogue with `codex plugin marketplace add bobyone/my-beautiful-choir`,
then install the plugin from the **My Beautiful Choir** marketplace in the
ChatGPT desktop app. Refresh the Git marketplace with
`codex plugin marketplace upgrade my-beautiful-choir`.

### Claude Code

The plugin is installed from the repository's own marketplace, declared in
the `.claude/settings.local.json` of the project that needs it (never in a
committed settings file nor in user settings):

```json
{
  "extraKnownMarketplaces": {
    "my-beautiful-choir": {
      "source": { "source": "github", "repo": "bobyone/my-beautiful-choir" }
    }
  },
  "enabledPlugins": { "my-beautiful-choir@my-beautiful-choir": true }
}
```

Then guide the user to turn on automatic updates for this marketplace in
Claude Code: `/plugin` → *Marketplaces* → my-beautiful-choir.

## When something fails

Use the `troubleshoot` skill.

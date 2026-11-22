<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Quick-start

my-beautiful-choir is not published yet: for now, it runs from a clone of
the repository. Once released, personal mode will be launched with
`uvx my-beautiful-choir`.

## Personal mode, from a clone

For Claude Desktop or ChatGPT desktop with local Codex, start with the
[desktop installation commands](how-to/install-desktop-clients.md).
The manual setup below also works for compatible local MCP clients.

Prerequisites: [Git](https://git-scm.com/), [uv](https://docs.astral.sh/uv/)
and [Node.js](https://nodejs.org/) (LTS) to build the user interface.

1. Get the code and build the user interface:

   ```sh
   git clone https://github.com/bobyone/my-beautiful-choir.git
   cd my-beautiful-choir
   uv sync
   uv run nox -s ui
   ```

2. Declare the server in your MCP client. For Claude Desktop, add to its
   configuration file (*Settings → Developer → Edit config*), with the
   absolute path of your clone:

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

3. Restart the client and ask: *"Show me information about
   my-beautiful-choir."* The `show_about` tool displays the "About" view.

If it does not start, see
[how to troubleshoot a startup failure](how-to/troubleshoot-startup.md).

### Try the repertoire

Ask the assistant to create your first choir by name, add a work, then
show the choir's repertoire. Search by title or composer and select a
work to see its scores. Choose **Add a score** in the Work view to import
a file. You can also ask the assistant to import a score from an absolute
local path or a public Google Drive link.

The repertoire database and score files live in the personal data
directory. See [back up and restore personal data](how-to/back-up-and-restore-personal-data.md).

## Web mode, with Docker Compose

> Web mode has no authentication yet: never expose it publicly. The
> provided `compose.yaml` publishes the port on the local host only.

Prerequisite: [Docker](https://docs.docker.com/get-docker/) with Compose.

1. From the clone, optionally copy the example configuration and adjust it
   (see the [configuration reference](configuration.md)):

   ```sh
   cp .env.example .env
   ```

2. Build and start the service:

   ```sh
   docker compose up --detach --build
   ```

3. Check that it is ready: `http://localhost:9000/healthz` answers
   `{"status": "ready"}`.

4. Declare the server in your MCP client, as a Streamable HTTP server at
   `http://localhost:9000/mcp`.

Read the logs with `docker compose logs`, stop with `docker compose down`.

## Plugin skills

See [how to install the plugin in Codex](how-to/install-the-plugin-in-codex.md)
to use the application's skills from Codex.

## Development setup

See [CONTRIBUTING.md](../CONTRIBUTING.md) to install the development
environment, run the checks and contribute.

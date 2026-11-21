<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Quick-start

my-beautiful-choir is not published yet: for now, it runs from a clone of
the repository. Once released, personal mode will be launched with
`uvx my-beautiful-choir`.

## Personal mode, from a clone

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

## Web mode

See the next section once the container image is available. Web mode has
no authentication yet: never expose it publicly.

## Development setup

See [CONTRIBUTING.md](../CONTRIBUTING.md) to install the development
environment, run the checks and contribute.

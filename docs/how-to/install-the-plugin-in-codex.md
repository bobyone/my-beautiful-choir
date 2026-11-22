<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Install the plugin in Codex

The plugin adds the user skills for my-beautiful-choir. Set up the MCP
server separately using the [quick-start](../quick-start.md).

1. Add the project's Git marketplace from the Codex CLI:

   ```sh
   codex plugin marketplace add bobyone/my-beautiful-choir
   ```

2. Restart the ChatGPT desktop app. In the Plugins Directory, select the
   **My Beautiful Choir** marketplace and install **my-beautiful-choir**.
3. Open a new Codex conversation and ask how to install my-beautiful-choir
   to check that the install skill is available.

Refresh the tracked marketplace when it changes:

```sh
codex plugin marketplace upgrade my-beautiful-choir
```

Restart the desktop app after refreshing. See the
[Codex plugin documentation](https://developers.openai.com/plugins/build/plugins)
for marketplace availability and refresh behavior on your client.

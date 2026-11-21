<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# my-beautiful-choir

A choir management application inside your AI system.

my-beautiful-choir is an **MCP app**: an MCP server whose tools come with
interactive views rendered by your MCP client (Claude, ChatGPT, VS Code and
any other host supporting MCP Apps). It runs in two modes:

- **web mode**: a hosted service over HTTP, for several choirs, with user
  accounts and administration;
- **personal mode**: a local process over stdio, to manage your own choirs
  on your own computer.

The first version covers the choir's repertoire and scores.

> **Status:** pre-alpha, under initialization
> ([#1](https://github.com/bobyone/my-beautiful-choir/issues/1)).

## Documentation

- [Quick-start](docs/quick-start.md)
- [Architecture](docs/architecture.md)
- [How-to guides](docs/how-to/)
- [Glossary](docs/glossary.md)
- [Architecture decision records](docs/decisions/)
- [Records of processing](docs/privacy/records-of-processing.md)
- [Changelog](CHANGELOG.md)

## Contributing

Contributions are welcome: read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[code of conduct](CODE_OF_CONDUCT.md). To report a vulnerability, follow
[SECURITY.md](SECURITY.md).

## Licence

my-beautiful-choir is free software, licensed under the
[GNU General Public License, version 2 or later](LICENSE)
(`GPL-2.0-or-later`). The project follows the [REUSE](https://reuse.software)
specification. The licences of the libraries bundled into the user
interface are listed in `THIRD-PARTY-LICENSES.md`, next to the views in the
installed package.

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# How to build and check the user interface

The views (MCP Apps) live in `ui/`: React, react-bootstrap and the
`@modelcontextprotocol/ext-apps` SDK, in TypeScript, built by Vite into one
self-contained HTML file per view. Node.js (LTS) is needed to build them,
never to run my-beautiful-choir.

## Build the views

```sh
uv run nox -s ui
```

The session installs the locked dependencies (`npm ci`) the first time,
builds the views, then copies them, with the licence notices of the bundled
libraries (`THIRD-PARTY-LICENSES.md`), into
`src/my_beautiful_choir/views/static/`. That folder is not versioned: build
the views after cloning, and after every change in `ui/`, before running
my-beautiful-choir from the repository. Without them, it stops at startup
with the error `MBC-INSTALL`.

Add `-- --fresh` to reinstall the dependencies, for instance after
`ui/package-lock.json` changed: `uv run nox -s ui -- --fresh`.

## Check the views

```sh
uv run nox -s ui_check   # lint and format, types, tests with coverage, catalogues
uv run nox -s ui_audit   # known vulnerabilities, licences of the bundled libraries
```

`ui_check` is part of the default checks (`uv run nox`) and of the
pre-commit hook.

## Work on a view

From `ui/`:

| Command | What it does |
|---|---|
| `npm run test -- --watch` | Runs the tests on every change. |
| `npm run format` | Formats the code and applies automatic lint fixes. |
| `npm run build` | Builds each HTML entry under `ui/views/` into a standalone file in `ui/dist/views/` and combines their third-party notices. |

A view is tested without a host: tests replace the ext-apps React hooks
with a fake host (`src/test/fakeHost.ts`) that sends tool results and host
context changes.

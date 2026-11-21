<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 7. MCP Apps user interface stack

- Status: accepted
- Date: 2026-11-21
- Issue: #1

## Context

MCP Apps interfaces are HTML documents served as `ui://` resources and
rendered by the host in a sandboxed iframe. They communicate with the host
through the MCP Apps protocol, receive the host context (theme, locale,
time zone, display mode) and must meet WCAG 2.2 AA on desktop and mobile.

## Decision

| Concern | Tool |
|---|---|
| Language | TypeScript (strict) |
| MCP Apps protocol | `@modelcontextprotocol/ext-apps` |
| UI library | React with react-bootstrap (Bootstrap 5), themed through Bootstrap CSS variables mapped from the host theme |
| Build | Vite, bundled into one self-contained HTML file per view |
| Internationalization | i18next with ICU message format; `Intl` for dates, numbers and sorting |
| Package manager, lock file, audit | npm, `package-lock.json`, `npm audit` |
| Tests | Vitest, Testing Library, axe-core for accessibility checks |
| Lint and format | ESLint, Prettier |
| Licence compliance | `license-checker` |

The UI language and time zone come from the host context; the user can
override the language, and the choice is kept (in the account in web mode,
in local settings in personal mode).

The built HTML files are packaged inside the Python distribution; Node.js
is needed only to build, never at run time.

## Alternatives

- Plain TypeScript without a framework: lighter bundle, but more custom
  components.
- Another component library (Fluent UI, MUI): heavier, and further from the
  Bootstrap conventions used by the project.

## Consequences

- CI builds the UI before packaging the Python distribution.
- The host's content security policy forbids remote resources: all assets
  are inlined in the bundle.

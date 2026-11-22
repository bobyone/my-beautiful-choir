<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Contributing to my-beautiful-choir

Thank you for your interest! This guide is the project's contribution
how-to: every contributor, human or AI assistant, follows it.

## 1. Start with an issue

Every change starts with an issue, before any code:

- report a bug with the **Bug report** template;
- propose a change with the **Feature request** template.

Issues accessible to newcomers are labelled `good first issue`.

## 2. Get the design validated

Before writing code for a feature or a restructuring, the design is
validated by a maintainer **in the issue**, step by step. Wait for the
maintainer's agreement at the end of each step before moving on.

0. **Framing**: goal, acceptance criteria, out of scope, constraints.
1. **Abstract model and algorithm**: data (attributes, relations, states,
   invariants) and numbered algorithm steps, in business terms only, using
   the [glossary](docs/glossary.md). New terms come with a proposed
   definition.
2. **Design**: abstractions and their contracts, hierarchy, design patterns,
   alternatives considered, exceptions, dependency assembly, test strategy,
   screens and user journeys, file tree, optionally a Mermaid class diagram.
3. **Impacts and delivery**: changed code, compatibility and migrations, new
   dependencies, tests, documentation, privacy, licences, security, delivery
   plan.

Typo fixes and local bug fixes that touch no abstraction skip this step.
Each architecture decision becomes an ADR in
[docs/decisions/](docs/decisions/).

## 3. Set up the development environment

Prerequisites: [Git](https://git-scm.com/), [uv](https://docs.astral.sh/uv/)
(it installs the right Python version), and [Node.js](https://nodejs.org/)
(LTS, on the PATH) to build and check the user interface.

```sh
# Fork the repository on GitHub, then:
git clone https://github.com/<your-account>/my-beautiful-choir.git
cd my-beautiful-choir
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
uv run nox -s ui
```

To fix a translation or add a language, follow
[the dedicated how-to](docs/how-to/add-a-language.md).

For Codex contributions, start with [AGENTS.md](AGENTS.md) and the
repository contribution skill. In a trusted checkout, enable the project
hook when Codex asks for approval. It uses Git and uv from the PATH.
The repository permission profile and command rules apply where supported
by the active client and its managed settings.

## 4. Run the tests and checks

All checks are defined once, as [nox](https://nox.thea.codes/) sessions,
and used by the pre-commit hook and CI alike:

| Command | What it does |
|---|---|
| `uv run nox` | default checks: lint, types, tests with coverage, REUSE, user interface |
| `uv run nox -s ui` | builds the views into the Python package (needed to run the application) |
| `uv run nox -s ui_check` | user interface: lint and format, types, tests with coverage, translation catalogues |
| `uv run nox -s ui_audit` | user interface: known vulnerabilities, licences of bundled libraries |
| `uv run nox -s package` | builds the views, the wheel and the sdist, and checks the views are packaged |
| `uv run nox -s docker_check` | builds the web mode image, starts it and waits for its health check (needs Docker) |
| `uv run nox -s format` | formats the code and applies automatic fixes |
| `uv run nox -s lint` | style and formatting (ruff) |
| `uv run nox -s typecheck` | static types (mypy, strict) |
| `uv run nox -s tests` | tests, with a coverage threshold of 90 % |
| `uv run nox -s reuse` | licence and copyright of every file |
| `uv run nox -s audit` | known vulnerabilities in dependencies |
| `uv run nox -s licenses` | licence compatibility of runtime dependencies |
| `uv run nox -s dco -- origin/main..HEAD` | sign-off of your commits |

Never bypass the hook (`--no-verify`): fix the failure instead.

## 5. Follow the conventions

### Architecture

- Interfaces (abstract classes, protocols) are separated from their
  implementations; business logic only depends on abstractions.
- Hierarchy goes from the general concept to the concrete implementation.
  Each abstraction and each implementation lives in its own file; one
  directory per notion, with the general abstraction at its root and
  specializations in sub-directories.
- Dependencies are injected; concrete implementations are chosen and
  assembled only at the entry point, with `dependency-injector`.
- Configuration is read once at the entry point, then injected.

### Code

- Everything in the code is in English: identifiers, comments, docstrings,
  logs, error messages, file names.
- Code is fully typed and passes mypy in strict mode.
- Use the standard `logging` module, never `print`. Never log secrets or
  personal data.
- Define exceptions specific to each notion.
- New dependencies are discussed in the issue first.
- Keep changes focused: do not reformat unrelated code.

### Tests

- Every implementation has unit tests; core logic is tested with test
  doubles of its abstractions.
- Implementations touching an external system (database, files, network)
  also have integration tests.
- The test tree mirrors the code tree.

### Glossary and user interface

- One notion, one term, everywhere: interface, messages, documentation,
  code. Add a term to the [glossary](docs/glossary.md) before using it.
- No user-facing text is hard-coded: everything goes through translation
  keys, with named parameters and plural rules.

### Documentation

- Documentation is written in English and updated in the same commit as
  the code it describes.
- Every notable change is added to [CHANGELOG.md](CHANGELOG.md), under
  *Unreleased*, with its issue number.
- Update the plugin skills (`skills/`) and development skills
  (`.claude/skills/`, `.agents/skills/`) in the same commit as the behaviour
  they describe. Keep the versions in `plugin.json` and
  `.claude-plugin/plugin.json` aligned with the version in `pyproject.toml`.
- Changes to personal data processing update the
  [records of processing](docs/privacy/records-of-processing.md).

### Licences and authorship

- Every file starts with an SPDX header; files that cannot hold one are
  covered by [REUSE.toml](REUSE.toml).
- When you create or significantly modify a file, add your line to its
  header, with your forge account (never your e-mail address):

  ```text
  SPDX-FileContributor: <your-account>
  ```

- Add yourself to [CONTRIBUTORS.md](CONTRIBUTORS.md).

### Branches and commits

- Branch name: `<issue-number>-<short-description>`, for example
  `42-score-upload`.
- Atomic commits, short explicit messages in English, prefixed with the
  issue number: `#42 - Add score upload tool`.
- Every commit is signed off under the
  [Developer Certificate of Origin](https://developercertificate.org/):
  use `git commit -s`.

## 6. Submit the pull request

- Open it from your fork, against `main`, in English, with
  `Closes #<issue-number>`.
- Fill in the *definition of done* checklist of the template.
- CI must be green; a maintainer reviews the pull request before merging.
  Reply to each review comment; the reviewer resolves the threads.

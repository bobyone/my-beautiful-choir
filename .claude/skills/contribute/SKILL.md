---
name: contribute
description: Use when contributing to the my-beautiful-choir repository - starting work on an issue, validating a design, setting up the environment, running checks, committing, or opening a pull request. Guides the contributor step by step from the issue to the pull request, following CONTRIBUTING.md.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Contribute to my-beautiful-choir

`CONTRIBUTING.md` is the reference: read the section matching the current
step and apply it. This skill only gives the order of the steps and the
commands to run.

## 1. Issue

- Find the issue the work belongs to (`gh issue view <number>`). If there is
  none, help the contributor open one with the issue templates, then wait
  for a maintainer's agreement on the need.

## 2. Design

- Unless the change is a typo or a local bug fix touching no abstraction,
  present the design in the issue, step by step (steps 0 to 3 of
  CONTRIBUTING.md), and wait for the maintainer's agreement after each step.
- Use only terms from `docs/glossary.md`; propose a definition for any new
  term.

## 3. Environment

```sh
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

## 4. Branch

```sh
git switch -c <issue-number>-<short-description>
```

## 5. Implementation

- Follow the validated design; if the code shows it must change, stop and
  propose the change in the issue.
- Write the tests with the code, update the documentation, glossary,
  `CHANGELOG.md`, skills, records of processing, SPDX headers and
  `CONTRIBUTORS.md` in the same commits.
- Run the checks before each commit: `uv run nox`.

## 6. Commits

```sh
git commit -s -m "#<issue-number> - <short message in English>"
```

Never bypass the hooks. If a check fails, fix it.

## 7. Pull request

1. Run the CI-only checks: `uv run nox -s audit licenses` and
   `uv run nox -s dco -- origin/main..HEAD`.
2. Push the branch to the fork and open the pull request with the template:

   ```sh
   gh pr create --repo bobyone/my-beautiful-choir --fill-first
   ```

3. Fill in the definition of done checklist; each item not applicable is
   checked with "N/A" and the reason.
4. Address every review comment with a commit or an explanation; let the
   reviewer resolve the threads.

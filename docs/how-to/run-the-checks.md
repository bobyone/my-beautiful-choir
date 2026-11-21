<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# How to run the tests and checks

All checks are [nox](https://nox.thea.codes/) sessions defined in
[noxfile.py](../../noxfile.py). The pre-commit hook and CI call the same
sessions, so a green local run means a green CI run (on the same operating
system).

1. Install the environment once: `uv sync`.
2. Run the default checks (lint, types, tests with coverage, REUSE):

   ```sh
   uv run nox
   ```

3. Run a single session, for example the tests, with extra pytest
   arguments after `--`:

   ```sh
   uv run nox -s tests -- -k version
   ```

4. Run the checks that only CI runs by default:

   ```sh
   uv run nox -s audit licenses
   uv run nox -s dco -- origin/main..HEAD
   ```

5. Fix formatting and automatic lint findings: `uv run nox -s format`.

List all sessions with `uv run nox --list`.

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Quick-start

> my-beautiful-choir is under initialization: it cannot be run yet. This
> guide will describe, in a few steps, how to run personal mode with `uvx`
> and web mode with `docker compose`.

## Development setup

```sh
git clone https://github.com/bobyone/my-beautiful-choir.git
cd my-beautiful-choir
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
uv run nox
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full contribution guide.

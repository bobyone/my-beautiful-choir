# syntax=docker/dockerfile:1
# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

# Web mode image of my-beautiful-choir. Base images are pinned by version and
# digest; Dependabot keeps them up to date.

# --- Build the views (Node.js is only needed here) ---
FROM node:26-slim@sha256:e6bedef217677b276c591795e169840edd9096dbf13f29df8ef8d1856b8820bc AS ui
WORKDIR /build/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci --no-fund --no-audit
COPY ui/ ./
RUN npm run build

# --- Build the Python environment ---
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY LICENSES/ ./LICENSES/
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ ./src/
COPY --from=ui /build/ui/dist/views/ ./src/my_beautiful_choir/views/static/
COPY --from=ui /build/ui/dist/.vite/license.md ./src/my_beautiful_choir/views/static/THIRD-PARTY-LICENSES.md
RUN uv sync --frozen --no-dev --no-editable

# --- Runtime: no build tool, no development dependency, non-root user ---
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS runtime
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin choir
COPY --from=build /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    MBC_MODE=web \
    MBC_WEB__HOST=0.0.0.0 \
    MBC_WEB__PORT=9000
USER 10001
EXPOSE 9000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --start-interval=2s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.environ.get('MBC_WEB__PORT', '9000')}/healthz\", timeout=4)"]
CMD ["my-beautiful-choir"]

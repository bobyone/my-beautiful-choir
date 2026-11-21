# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Serialized metrics, ready to be served."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricsExport:
    """Metrics serialized in a monitoring format, with its media type."""

    content_type: str
    body: bytes

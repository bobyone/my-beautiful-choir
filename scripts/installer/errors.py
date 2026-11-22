# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""User-facing failures from the installer."""


class InstallationError(Exception):
    """Installation stopped before completing the requested change."""

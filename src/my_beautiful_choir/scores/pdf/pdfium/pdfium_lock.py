# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Serialize access to PDFium across personal-mode adapters."""

from threading import Lock

PDFIUM_LOCK = Lock()

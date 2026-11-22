# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Removal of the stored contents of deleted scores."""

import logging
from collections.abc import Iterable

from my_beautiful_choir.storage.file_storage import FileStorage

_LOGGER = logging.getLogger(__name__)


async def remove_stored_contents(file_storage: FileStorage, keys: Iterable[str]) -> None:
    """Delete the stored contents under ``keys``, once their scores are deleted or not saved.

    A content that cannot be deleted is logged and left: its score is already
    gone, so it is only wasted space, and the other contents are still removed.
    """
    for key in keys:
        try:
            await file_storage.delete(key)
        except Exception:
            _LOGGER.exception(
                "A stored content could not be deleted and is left", extra={"key": key}
            )

# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Startup step preparing the data directory and the database."""

import logging
from pathlib import Path

from my_beautiful_choir.application.startup_step import StartupStep
from my_beautiful_choir.persistence.errors import DataStoreError
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase

_LOGGER = logging.getLogger(__name__)

_WRITE_PROBE = ".write-probe"


class PrepareDataStore(StartupStep):
    """Creates the data directory, checks it is writable, then migrates the database."""

    def __init__(self, data_dir: Path, database: SqlDatabase) -> None:
        self._data_dir = data_dir
        self._database = database

    @property
    def name(self) -> str:
        """``prepare data store``."""
        return "prepare data store"

    async def run(self) -> None:
        """Prepare the data store.

        Raises:
            DataStoreError: if the directory cannot be created or written, or the
                migration fails.
        """
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            probe = self._data_dir / _WRITE_PROBE
            probe.write_bytes(b"")
            probe.unlink()
        except OSError as error:
            raise DataStoreError(self._data_dir, error.strerror or str(error)) from error
        try:
            await self._database.migrate()
        except Exception as error:
            _LOGGER.exception("Database migration failed")
            raise DataStoreError(self._data_dir, "the database migration failed") from error
        _LOGGER.info(
            "Data store ready",
            extra={"revision": await self._database.current_revision()},
        )

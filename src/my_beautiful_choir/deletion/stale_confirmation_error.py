# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""The state covered by a deletion confirmation has changed."""

from my_beautiful_choir.confirmation.errors import ConfirmationError
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview


class StaleConfirmationError(ConfirmationError):
    """The deletion needs a fresh confirmation."""

    def __init__(self, preview: DeletionPreview) -> None:
        super().__init__("The deletion preview changed and needs a new confirmation")
        self.preview = preview

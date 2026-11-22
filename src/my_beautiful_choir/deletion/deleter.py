# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Deleter abstraction."""

from abc import ABC, abstractmethod
from uuid import UUID

from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview


class Deleter(ABC):
    """Describes and performs the deletion of one kind of element.

    Describing changes nothing, so that the user can be asked to confirm
    first. Deleting removes the element, everything it contains, and their
    stored contents.
    """

    @property
    @abstractmethod
    def deletion_target(self) -> DeletionTarget:
        """Kind of element this deleter removes."""

    @abstractmethod
    async def describe_deletion(self, target_id: UUID) -> DeletionPreview:
        """What deleting the element would remove; changes nothing.

        Raises:
            DomainError: if the element does not exist (``ChoirNotFoundError``,
                ``WorkNotFoundError``, ``ScoreNotFoundError``) or may not be deleted.
        """

    @abstractmethod
    async def delete(self, preview: DeletionPreview) -> Deletion:
        """Delete the element and everything it contains; return what was removed.

        Raises:
            DomainError: if the element does not exist or may not be deleted.
            StaleConfirmationError: if its state no longer matches the preview.
        """

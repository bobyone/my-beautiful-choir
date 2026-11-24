# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Structured content and English texts shared by the deletion tools."""

from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import cast
from uuid import UUID

from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget


class DeletionStatus(StrEnum):
    """Where a deletion stands, as shown by the "Deletion" view."""

    DELETED = "deleted"
    """Done."""

    REFUSED = "refused"
    """The user refused: nothing was deleted."""

    PENDING = "pending"
    """Awaiting the user's confirmation in the view, under a token."""


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def deletion_label(deletion: Deletion) -> str:
    """What the deletion removes, in English: 'the work "Ave Maria" of the choir "Chœur"…'."""
    label = f'the {deletion.target.value} "{deletion.name}"'
    match deletion.target:
        case DeletionTarget.WORK:
            label += f' of the choir "{deletion.parent_name}"'
        case DeletionTarget.SCORE:
            label += f' of the work "{deletion.parent_name}"'
        case DeletionTarget.CHOIR:
            pass
    contents = [
        _count(count, noun)
        for count, noun in ((deletion.work_count, "work"), (deletion.score_count, "score"))
        if count
    ]
    if contents:
        label += " with its " + " and ".join(contents)
    return label


def deletion_question(deletion: Deletion) -> str:
    """Question asked to the user before deleting."""
    return f"Delete {deletion_label(deletion)}? This cannot be undone."


def deletion_data(
    status: DeletionStatus, deletion: Deletion, token: str | None = None
) -> Mapping[str, object]:
    """Structured content displayed by the "Deletion" view."""
    data: dict[str, object] = {
        "status": status.value,
        "deletion": {
            "target": deletion.target.value,
            "id": str(deletion.target_id),
            "name": deletion.name,
            "parent_name": deletion.parent_name,
            "work_count": deletion.work_count,
            "score_count": deletion.score_count,
            **(
                {"movement_number": deletion.movement_number}
                if deletion.movement_number is not None
                else {}
            ),
            **({"added_at": deletion.added_at.isoformat()} if deletion.added_at else {}),
        },
    }
    if token is not None:
        data["token"] = token
    return data


def deletion_from_data(data: Mapping[str, object]) -> Deletion:
    """The deletion described by structured content made by ``deletion_data``."""
    described = cast(Mapping[str, object], data["deletion"])
    parent_name = described["parent_name"]
    movement_number = described.get("movement_number")
    added_at = described.get("added_at")
    return Deletion(
        target=DeletionTarget(str(described["target"])),
        target_id=UUID(str(described["id"])),
        name=str(described["name"]),
        parent_name=None if parent_name is None else str(parent_name),
        work_count=int(str(described["work_count"])),
        score_count=int(str(described["score_count"])),
        movement_number=None if movement_number is None else int(str(movement_number)),
        added_at=None if added_at is None else datetime.fromisoformat(str(added_at)),
    )


def describe_deletion_data(data: Mapping[str, object]) -> str:
    """Text result of a deletion tool, for the model."""
    label = deletion_label(deletion_from_data(data))
    match DeletionStatus(str(data["status"])):
        case DeletionStatus.DELETED:
            return f"Deleted {label}."
        case DeletionStatus.REFUSED:
            return f"The user refused to delete {label}: nothing was deleted."
        case DeletionStatus.PENDING:
            return (
                f"Nothing is deleted yet: the user must confirm the deletion of {label} with "
                "the Delete button of the view shown. Do not call the tool again."
            )

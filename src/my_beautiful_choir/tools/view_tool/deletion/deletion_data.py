# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Structured content and English texts shared by the deletion tools."""

from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import cast
from uuid import UUID

from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.scores.score_state import ScoreState


class DeletionStatus(StrEnum):
    """Where a deletion stands, as shown by the "Deletion" view."""

    DELETED = "deleted"
    """Done."""

    REFUSED = "refused"
    """The user refused: nothing was deleted."""

    PENDING = "pending"
    """Awaiting the user's confirmation in the view, under a token."""


def _count(number: int, noun: str, plural: str | None = None) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {plural or noun + 's'}"


def deletion_label(deletion: Deletion) -> str:
    """What the deletion removes, in English: 'the work "Ave Maria" of the choir "Chœur"…'."""
    kind = deletion.event_kind.value if deletion.event_kind else deletion.target.value
    label = f'the {kind} "{deletion.name}"'
    match deletion.target:
        case DeletionTarget.WORK:
            label += f' of the choir "{deletion.parent_name}"'
        case DeletionTarget.SCORE:
            match deletion.score_state:
                case ScoreState.DRAFT:
                    label += " (draft)"
                case ScoreState.FINAL:
                    label += f" (final v{deletion.version_number})"
            label += f' of the work "{deletion.parent_name}"'
        case DeletionTarget.EVENT:
            if deletion.starts_at is not None:
                label += f" starting {deletion.starts_at.isoformat()}"
            label += f' of the choir "{deletion.parent_name}"'
        case DeletionTarget.CHOIR:
            pass
    contents = [
        _count(count, noun, plural)
        for count, noun, plural in (
            (deletion.work_count, "work", None),
            (deletion.score_count, "score", None),
            (deletion.programme_entry_count, "programme entry", "programme entries"),
        )
        if count
    ]
    if deletion.target is DeletionTarget.CHOIR and deletion.event_count:
        contents.append(_count(deletion.event_count, "event"))
    if contents:
        label += " with its " + " and ".join(contents)
    if deletion.target is DeletionTarget.WORK and deletion.event_count:
        label += (
            f", which stays without a link in the programme of "
            f"{_count(deletion.event_count, 'event')}"
        )
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
            **({"score_state": deletion.score_state.value} if deletion.score_state else {}),
            **({"version_number": deletion.version_number} if deletion.version_number else {}),
            **({"added_at": deletion.added_at.isoformat()} if deletion.added_at else {}),
            **({"event_count": deletion.event_count} if deletion.event_count else {}),
            **({"event_kind": deletion.event_kind.value} if deletion.event_kind else {}),
            **({"starts_at": deletion.starts_at.isoformat()} if deletion.starts_at else {}),
            **(
                {"programme_entry_count": deletion.programme_entry_count}
                if deletion.programme_entry_count
                else {}
            ),
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
    starts_at = described.get("starts_at")
    return Deletion(
        target=DeletionTarget(str(described["target"])),
        target_id=UUID(str(described["id"])),
        name=str(described["name"]),
        parent_name=None if parent_name is None else str(parent_name),
        work_count=int(str(described["work_count"])),
        score_count=int(str(described["score_count"])),
        movement_number=None if movement_number is None else int(str(movement_number)),
        added_at=None if added_at is None else datetime.fromisoformat(str(added_at)),
        score_state=ScoreState(str(described["score_state"]))
        if "score_state" in described
        else None,
        version_number=int(str(described["version_number"]))
        if "version_number" in described
        else None,
        event_count=int(str(described.get("event_count", 0))),
        event_kind=EventKind(str(described["event_kind"])) if "event_kind" in described else None,
        starts_at=None if starts_at is None else datetime.fromisoformat(str(starts_at)),
        programme_entry_count=int(str(described.get("programme_entry_count", 0))),
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

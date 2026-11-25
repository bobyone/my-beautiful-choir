# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Project musical data for MCP, keeping untrusted text in bounded fields."""

from collections.abc import Mapping
from typing import cast

from my_beautiful_choir.configuration.score_reading_settings import ScoreReadingSettings
from my_beautiful_choir.scores.reading.event_location import EventLocation
from my_beautiful_choir.scores.reading.musical_event import MusicalEvent
from my_beautiful_choir.scores.reading.notation import Notation
from my_beautiful_choir.scores.reading.notation_span import NotationSpan
from my_beautiful_choir.scores.reading.pitch import Pitch

_LABELS = {"label", "before_labels", "after_labels"}


class ReadingProjection:
    """Serialise exchange notation and mark omitted free text explicitly."""

    def __init__(self, settings: ScoreReadingSettings) -> None:
        self._settings = settings

    def record(
        self, value: Mapping[str, object], *, pitch_mode: str = "written"
    ) -> dict[str, object]:
        """Project a report record into finite JSON data."""
        return {key: self._value(item, key, pitch_mode) for key, item in value.items()}

    def _value(self, value: object, field: str, pitch_mode: str) -> object:
        if isinstance(value, MusicalEvent):
            return self._event(value, pitch_mode)
        if isinstance(value, Pitch):
            return {"step": value.step, "octave": value.octave, "alter": str(value.alter)}
        if isinstance(value, Notation):
            return self._notation(value, self._settings.other_text_chars)
        if isinstance(value, NotationSpan):
            return {
                "kind": value.kind,
                "start": self._value(value.start, field, pitch_mode),
                "end": self._value(value.end, field, pitch_mode),
            }
        if isinstance(value, EventLocation):
            return {"measure": value.measure, "event": value.event}
        if isinstance(value, (list, tuple)):
            return [self._value(item, field, pitch_mode) for item in value]
        if isinstance(value, Mapping):
            return self.record(cast(Mapping[str, object], value), pitch_mode=pitch_mode)
        if isinstance(value, str):
            if field in _LABELS:
                return _bounded(value, self._settings.label_chars)
            if field in {"staff", "voice", "verse", "feature", "unsupported"}:
                return _bounded(value, self._settings.other_text_chars)
        return value

    def _event(self, event: MusicalEvent, pitch_mode: str) -> dict[str, object]:
        data: dict[str, object] = {"kind": event.kind, "offset": str(event.offset)}
        if event.duration is not None:
            data["duration"] = str(event.duration)
        for field, value in (("staff", event.staff), ("voice", event.voice)):
            if value is not None:
                data[field] = self._value(value, field, pitch_mode)
        if event.pitch:
            if pitch_mode == "written":
                data["pitch"] = self._value(event.pitch, "pitch", pitch_mode)
            elif event.sounding is None:
                data["pitch"] = None
                data["written_pitch"] = self._value(event.pitch, "pitch", "written")
            else:
                data["pitch"] = [str(height) for height in event.sounding]
                data["written_pitch"] = self._value(event.pitch, "pitch", "written")
        if event.details:
            data["details"] = [
                self._notation(item, self._settings.other_text_chars) for item in event.details
            ]
        return data

    def _notation(self, notation: Notation, limit: int) -> dict[str, object]:
        if notation.kind == "lyric":
            limit = self._settings.lyric_chars
        elif notation.kind in {"direction", "direction-type", "words"}:
            limit = self._settings.direction_chars
        result: dict[str, object] = {"kind": notation.kind}
        if notation.value:
            result["value"] = _bounded(notation.value, limit)
        if notation.properties:
            result["properties"] = [
                [_bounded(name, self._settings.other_text_chars), _bounded(value, limit)]
                for name, value in notation.properties
            ]
        if notation.details:
            result["details"] = [self._notation(child, limit) for child in notation.details]
        return result


def _bounded(text: str, limit: int) -> str | dict[str, bool]:
    return text if len(text) <= limit else {"omitted": True}

# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Selection of the mode container: the single point where implementations are chosen."""

from dependency_injector import containers

from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.containers.application_container import ApplicationContainer
from my_beautiful_choir.containers.personal_mode_container import PersonalModeContainer
from my_beautiful_choir.containers.web_mode_container import WebModeContainer

MODE_CONTAINERS: dict[Mode, type[containers.DeclarativeContainer]] = {
    Mode.PERSONAL: PersonalModeContainer,
    Mode.WEB: WebModeContainer,
}


def create_container(settings: Settings) -> ApplicationContainer:
    """Assemble the application for the mode given by ``settings``."""
    mode_container = MODE_CONTAINERS[settings.mode](settings=settings)
    return ApplicationContainer(settings=settings, mode=mode_container)

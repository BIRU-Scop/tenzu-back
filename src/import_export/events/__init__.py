# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 BIRU
#
# This file is part of Tenzu.
#
# Tenzu is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# You can contact BIRU at ask@biru.sh
from uuid import UUID

from events import events_manager
from import_export.events.content import (
    CreateProjectImportationContent,
    DeleteProjectImportationContent,
    UpdateProjectImportationContent,
)
from import_export.models import ProjectImportation
from users.models import User

CREATE_PROJECT_IMPORTATION = "projectimportations.create"
DELETE_PROJECT_IMPORTATION = "projectimportations.delete"
UPDATE_PROJECT_IMPORTATION = "projectimportations.update"


async def emit_event_when_project_importation_is_created(
    project_importation: ProjectImportation,
) -> None:
    """
    This event is emitted whenever a project importation is created
    """
    # for the creator on homepage or workspace detail
    await events_manager.publish_on_user_channel(
        user=project_importation.created_by,
        type=CREATE_PROJECT_IMPORTATION,
        content=CreateProjectImportationContent(
            project_importation=project_importation,
            workspace_id=project_importation.workspace_id,
        ),
    )


async def emit_event_when_project_importation_is_updated(
    project_importation: ProjectImportation,
) -> None:
    """
    This event is emitted whenever there's a change in the project importation
    """
    # for the creator on homepage or workspace detail
    await events_manager.publish_on_user_channel(
        user=project_importation.created_by_id,
        type=UPDATE_PROJECT_IMPORTATION,
        content=UpdateProjectImportationContent(
            project_importation=project_importation,
            workspace_id=project_importation.workspace_id,
        ),
    )


async def emit_event_when_project_importation_is_deleted(
    workspace_id: UUID,
    project_importation_id: UUID,
    importation_owner: User,
) -> None:
    """
    This event is emitted whenever a project importation is deleted
    """
    # for the creator on homepage or workspace detail
    await events_manager.publish_on_user_channel(
        user=importation_owner,
        type=DELETE_PROJECT_IMPORTATION,
        content=DeleteProjectImportationContent(
            project_importation_id=project_importation_id,
            workspace_id=workspace_id,
        ),
    )

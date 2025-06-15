# -*- coding: utf-8 -*-
# Copyright (C) 2024 BIRU
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
from projects.projects.events.content import (
    CreateProjectContent,
    DeleteProjectContent,
    UpdateProjectContent,
)
from projects.projects.models import Project
from projects.projects.serializers import ProjectDetailSerializer
from users.models import User

CREATE_PROJECT = "projects.create"
DELETE_PROJECT = "projects.delete"
UPDATE_PROJECT = "projects.update"


async def emit_event_when_project_is_created(project: Project) -> None:
    """
    This event is emitted whenever a project is created
    """
    # for the creator on homepage or workspace detail
    await events_manager.publish_on_user_channel(
        user=project.created_by,
        type=CREATE_PROJECT,
        content=CreateProjectContent(
            project=project,
            created_by_id=project.created_by_id,
            workspace_id=project.workspace_id,
        ),
    )
    # for other ws-member on workspace detail
    await events_manager.publish_on_workspace_channel(
        workspace=project.workspace_id,
        type=CREATE_PROJECT,
        content=CreateProjectContent(
            project=None,  # project detail is only sent to the creator since other ws-members do not have access to it
            created_by_id=project.created_by_id,
            workspace_id=project.workspace_id,
        ),
    )


async def emit_event_when_project_is_updated(
    project_detail: ProjectDetailSerializer, updated_by: User
) -> None:
    """
    This event is emitted whenever there's a change in the project
    :param project_detail: the detailed project affected by the changes
    :param updated_by: The user responsible for the changes
    """
    content = UpdateProjectContent(project=project_detail, updated_by=updated_by)
    # for pj-members and pj-invitees in the ws-detail
    await events_manager.publish_on_workspace_channel(
        workspace=project_detail.workspace_id,
        type=UPDATE_PROJECT,
        content=content,
    )
    # for pj-member in the project detail
    await events_manager.publish_on_project_channel(
        project=project_detail.id,
        type=UPDATE_PROJECT,
        content=content,
    )
    # TODO handle pj-members and pj-invitees on homepage


async def emit_event_when_project_is_deleted(
    workspace_id: UUID,
    project: Project,
    deleted_by: User,
) -> None:
    content = DeleteProjectContent(
        project_id=project.id,
        name=project.name,
        deleted_by=deleted_by,
        workspace_id=workspace_id,
    )
    # for pj-members and pj-invitees in the ws-detail
    await events_manager.publish_on_workspace_channel(
        workspace=workspace_id,
        type=DELETE_PROJECT,
        content=content,
    )

    # for pj-member in the project detail
    await events_manager.publish_on_project_channel(
        project=project,
        type=DELETE_PROJECT,
        content=content,
    )
    # TODO handle pj-members and pj-invitees on homepage

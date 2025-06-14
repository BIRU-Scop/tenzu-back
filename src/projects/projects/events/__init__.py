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
from projects.projects.events.content import DeleteProjectContent, UpdateProjectContent
from projects.projects.models import Project
from projects.projects.serializers import ProjectDetailSerializer
from users.models import User

PROJECT_DELETE = "projects.delete"
PROJECT_UPDATE = "projects.update"
PROJECT_PERMISSIONS_UPDATE = "projects.permissions.update"


async def emit_event_when_project_permissions_are_updated(project: Project) -> None:
    """
    This event is emitted whenever there's a change in the project's direct permissions (public / workspace permissions)
    :param project: The project affected by the permission change
    """
    await events_manager.publish_on_project_channel(
        project=project, type=PROJECT_PERMISSIONS_UPDATE
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
        type=PROJECT_UPDATE,
        content=content,
    )
    # for pj-member in the project detail
    await events_manager.publish_on_project_channel(
        project=project_detail.id,
        type=PROJECT_UPDATE,
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
        type=PROJECT_DELETE,
        content=content,
    )

    # for pj-member in the project detail
    await events_manager.publish_on_project_channel(
        project=project,
        type=PROJECT_DELETE,
        content=content,
    )
    # TODO handle pj-members and pj-invitees on homepage

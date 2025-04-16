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

from events import events_manager
from projects.projects.events.content import DeleteProjectContent, UpdateProjectContent
from projects.projects.models import Project
from projects.projects.serializers import ProjectDetailSerializer
from users.models import AnyUser, User
from workspaces.workspaces.models import Workspace

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
    project_detail: ProjectDetailSerializer, project_id: str, updated_by: User
) -> None:
    """
    This event is emitted whenever there's a change in the project
    :param project_detail: the detailed project affected by the changes
    :param project_id: the project id in b64 since the one stored in project_detail is not well formatted
    :param updated_by: The user responsible for the changes
    """
    await events_manager.publish_on_project_channel(
        project=project_id,
        type=PROJECT_UPDATE,
        content=UpdateProjectContent(project=project_detail, updated_by=updated_by),
    )


async def emit_event_when_project_is_deleted(
    workspace: Workspace,
    project: Project,
    deleted_by: User,
    guests: list[User],
) -> None:
    # for ws-members, both in the home page and in the ws-detail
    await events_manager.publish_on_workspace_channel(
        workspace=workspace,
        type=PROJECT_DELETE,
        content=DeleteProjectContent(
            project=project.id,
            name=project.name,
            deleted_by=deleted_by,
            workspace=workspace.id,
        ),
    )

    # for anyuser in the project detail
    await events_manager.publish_on_project_channel(
        project=project,
        type=PROJECT_DELETE,
        content=DeleteProjectContent(
            project=project.id,
            name=project.name,
            deleted_by=deleted_by,
            workspace=workspace.id,
        ),
    )

    # for ws-guests (pj-invitees) in the home page,
    # this is the only way we can notify the change
    for guest in guests:
        await events_manager.publish_on_user_channel(
            user=guest,
            type=PROJECT_DELETE,
            content=DeleteProjectContent(
                project=project.id,
                name=project.name,
                deleted_by=deleted_by,
                workspace=workspace.id,
            ),
        )

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
from users.models import AnyUser, User
from workspaces.workspaces.events.content import (
    CreateWorkspaceContent,
    DeleteWorkspaceContent,
    UpdateWorkspaceContent,
)
from workspaces.workspaces.models import Workspace
from workspaces.workspaces.serializers import WorkspaceDetailSerializer

CREATE_WORKSPACE = "workspaces.create"
UPDATE_WORKSPACE = "workspaces.update"
DELETE_WORKSPACE = "workspaces.delete"


async def emit_event_when_workspace_is_created(
    workspace_detail: WorkspaceDetailSerializer, created_by: User
) -> None:
    content = CreateWorkspaceContent(workspace=workspace_detail)
    # for creator other windows on homepage
    await events_manager.publish_on_user_channel(
        user=created_by,
        type=CREATE_WORKSPACE,
        content=content,
    )


async def emit_event_when_workspace_is_updated(
    workspace_detail: WorkspaceDetailSerializer, updated_by: User
) -> None:
    """
    This event is emitted whenever there's a change in the workspace
    :param workspace_detail: the detailed workspace affected by the changes
    :param updated_by: The user responsible for the changes
    """
    content = UpdateWorkspaceContent(workspace=workspace_detail, updated_by=updated_by)
    # for pj-members and pj-invitees in the ws-detail
    await events_manager.publish_on_workspace_channel(
        workspace=workspace_detail.id,
        type=UPDATE_WORKSPACE,
        content=content,
    )
    # TODO handle ws-members and ws-invitees on homepage


async def emit_event_when_workspace_is_deleted(
    workspace: Workspace, deleted_by: AnyUser
) -> None:
    # for ws-members, and in the ws-detail
    await events_manager.publish_on_workspace_channel(
        workspace=workspace,
        type=DELETE_WORKSPACE,
        content=DeleteWorkspaceContent(
            workspace_id=workspace.id, name=workspace.name, deleted_by=deleted_by
        ),
    )
    # TODO handle ws-members and ws-invitees on homepage

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
from users.models import AnyUser
from workspaces.workspaces.events.content import DeleteWorkspaceContent
from workspaces.workspaces.models import Workspace

WORKSPACE_DELETE = "workspaces.delete"


async def emit_event_when_workspace_is_deleted(workspace: Workspace, deleted_by: AnyUser) -> None:
    # for ws-members, both in the home page and in the ws-detail
    await events_manager.publish_on_workspace_channel(
        workspace=workspace,
        type=WORKSPACE_DELETE,
        content=DeleteWorkspaceContent(workspace=workspace.id, name=workspace.name, deleted_by=deleted_by),
    )

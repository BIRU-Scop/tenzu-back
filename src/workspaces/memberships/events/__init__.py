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
from workspaces.memberships.events.content import (
    WorkspaceMembershipContent,
)
from workspaces.memberships.models import WorkspaceMembership

UPDATE_WORKSPACE_MEMBERSHIP = "workspacememberships.update"
DELETE_WORKSPACE_MEMBERSHIP = "workspacememberships.delete"


async def emit_event_when_workspace_membership_is_updated(
    membership: WorkspaceMembership,
) -> None:
    content = WorkspaceMembershipContent(membership=membership)
    await events_manager.publish_on_user_channel(
        user=membership.user,
        type=UPDATE_WORKSPACE_MEMBERSHIP,
        content=content,
    )

    await events_manager.publish_on_workspace_channel(
        workspace=membership.workspace_id,
        type=UPDATE_WORKSPACE_MEMBERSHIP,
        content=content,
    )


async def emit_event_when_workspace_membership_is_deleted(
    membership: WorkspaceMembership,
) -> None:
    content = WorkspaceMembershipContent(membership=membership)
    await events_manager.publish_on_workspace_channel(
        workspace=membership.workspace,
        type=DELETE_WORKSPACE_MEMBERSHIP,
        content=content,
    )

    await events_manager.publish_on_user_channel(
        user=membership.user,
        type=DELETE_WORKSPACE_MEMBERSHIP,
        content=content,
    )

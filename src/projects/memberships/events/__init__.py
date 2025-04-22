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
from projects.memberships.events.content import (
    DeleteProjectMembershipContent,
    ProjectMembershipContent,
    ProjectRoleContent,
)
from projects.memberships.models import ProjectMembership, ProjectRole

CREATE_PROJECT_MEMBERSHIP = "projectmemberships.create"
UPDATE_PROJECT_MEMBERSHIP = "projectmemberships.update"
DELETE_PROJECT_MEMBERSHIP = "projectmemberships.delete"


async def emit_event_when_project_membership_is_created(
    membership: ProjectMembership,
) -> None:
    await events_manager.publish_on_user_channel(
        user=membership.user,
        type=CREATE_PROJECT_MEMBERSHIP,
        content=ProjectMembershipContent(membership=membership),
    )

    await events_manager.publish_on_project_channel(
        project=membership.project,
        type=CREATE_PROJECT_MEMBERSHIP,
        content=ProjectMembershipContent(membership=membership),
    )


async def emit_event_when_project_membership_is_updated(
    membership: ProjectMembership,
) -> None:
    await events_manager.publish_on_user_channel(
        user=membership.user,
        type=UPDATE_PROJECT_MEMBERSHIP,
        content=ProjectMembershipContent(membership=membership),
    )

    await events_manager.publish_on_project_channel(
        project=membership.project,
        type=UPDATE_PROJECT_MEMBERSHIP,
        content=ProjectMembershipContent(membership=membership),
    )


async def emit_event_when_project_membership_is_deleted(
    membership: ProjectMembership,
) -> None:
    # for anyuser in the project detail or pj-admins in setting members
    await events_manager.publish_on_project_channel(
        project=membership.project,
        type=DELETE_PROJECT_MEMBERSHIP,
        content=DeleteProjectMembershipContent(
            membership=membership, workspace_id=membership.project.workspace_id
        ),
    )

    # for deleted user in her home or in project detail
    await events_manager.publish_on_user_channel(
        user=membership.user,
        type=DELETE_PROJECT_MEMBERSHIP,
        content=DeleteProjectMembershipContent(
            membership=membership, workspace_id=membership.project.workspace_id
        ),
    )


UPDATE_PROJECT_ROLE_PERMISSIONS = "projectroles.update"


async def emit_event_when_project_role_is_updated(
    role: ProjectRole,
) -> None:
    """
    This event is emitted whenever the permissions list changes for a role
    :param role: The project role affected by the permission change
    """
    await events_manager.publish_on_project_channel(
        project=role.project,
        type=UPDATE_PROJECT_ROLE_PERMISSIONS,
        content=ProjectRoleContent.from_orm(role),
    )

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
from projects.memberships.events.content import (
    DeleteProjectMembershipContent,
    DeleteProjectRoleContent,
    ProjectMembershipContent,
    ProjectRoleContent,
)
from projects.memberships.models import ProjectMembership, ProjectRole
from projects.memberships.serializers import ProjectMembershipSerializer
from projects.projects.models import Project
from users.models import User

UPDATE_PROJECT_MEMBERSHIP = "projectmemberships.update"
DELETE_PROJECT_MEMBERSHIP = "projectmemberships.delete"


async def emit_event_when_project_membership_is_updated(
    membership: ProjectMembership, user: User = None, project: Project = None
) -> None:
    user = user or membership.user
    content = ProjectMembershipContent(
        membership=ProjectMembershipSerializer(
            project_id=membership.project_id,
            role_id=membership.role_id,
            id=membership.id,
            user=user,
        ),
        role=membership.role,
        project=project,
        self_recipient=True,
    )
    await events_manager.publish_on_user_channel(
        user=user,
        type=UPDATE_PROJECT_MEMBERSHIP,
        content=content,
    )
    content.self_recipient = False
    await events_manager.publish_on_project_channel(
        project=membership.project_id,
        type=UPDATE_PROJECT_MEMBERSHIP,
        content=content,
    )


async def emit_event_when_project_membership_is_deleted(
    membership: ProjectMembership, workspace_id: UUID, user: User = None
) -> None:
    user = user or membership.user
    content = DeleteProjectMembershipContent(
        membership=ProjectMembershipSerializer(
            project_id=membership.project_id,
            role_id=membership.role_id,
            id=membership.id,
            user=user,
        ),
        workspace_id=workspace_id,
        self_recipient=False,
    )
    # for anyuser in the project detail
    await events_manager.publish_on_project_channel(
        project=membership.project_id,
        type=DELETE_PROJECT_MEMBERSHIP,
        content=content,
    )
    content.self_recipient = True
    # for deleted user in home, workspace of project detail or project detail
    await events_manager.publish_on_user_channel(
        user=user,
        type=DELETE_PROJECT_MEMBERSHIP,
        content=content,
    )


CREATE_PROJECT_ROLE = "projectroles.create"
UPDATE_PROJECT_ROLE = "projectroles.update"
DELETE_PROJECT_ROLE = "projectroles.delete"


async def emit_event_when_project_role_is_created(
    role: ProjectRole,
) -> None:
    """
    This event is emitted whenever a role is created
    """
    await events_manager.publish_on_project_channel(
        project=role.project,
        type=CREATE_PROJECT_ROLE,
        content=ProjectRoleContent(role=role),
    )


async def emit_event_when_project_role_is_updated(
    role: ProjectRole,
) -> None:
    """
    This event is emitted whenever the permissions list or name changes for a role
    :param role: The project role affected by the permission change
    """
    await events_manager.publish_on_project_channel(
        project=role.project,
        type=UPDATE_PROJECT_ROLE,
        content=ProjectRoleContent(role=role),
    )


async def emit_event_when_project_role_is_deleted(
    role: ProjectRole, target_role: ProjectRole | None
) -> None:
    """
    This event is emitted whenever a role is deleted
    """
    await events_manager.publish_on_project_channel(
        project=role.project,
        type=DELETE_PROJECT_ROLE,
        content=DeleteProjectRoleContent(
            role_id=role.id,
            target_role=target_role,
            project_id=role.project_id,
        ),
    )

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

from projects.projects.models import Project
from projects.roles import events as pj_roles_events
from projects.roles import repositories as pj_roles_repositories
from projects.roles.models import ProjectRole
from projects.roles.services import exceptions as ex
from stories.assignments import repositories as story_assignments_repositories
from stories.stories import permissions as stories_permissions
from users.models import AnyUser

##########################################################
# list project roles
##########################################################


async def get_user_project_role_info(
    user: AnyUser, project: Project
) -> tuple[bool, bool, list[str]]:
    if user.is_anonymous:
        return False, False, []

    role = await pj_roles_repositories.get_project_role(
        filters={"user_id": user.id, "project_id": project.id}
    )
    if role:
        return role.is_admin, True, role.permissions

    return False, False, []


async def list_project_roles(project: Project) -> list[ProjectRole]:
    return await pj_roles_repositories.list_project_roles(
        filters={"project_id": project.id}
    )


async def list_project_roles_as_dict(project: Project) -> dict[str, ProjectRole]:
    """
    This method forms a custom dictionary with the roles matching a project
    :param project: The project to get their roles from
    :return: Dictionary whose key is the role slug and value the Role object
    """

    return {
        r.slug: r
        for r in await pj_roles_repositories.list_project_roles(
            filters={"project_id": project.id}
        )
    }


##########################################################
# get project role
##########################################################


async def get_project_role(project_id: UUID, slug: str) -> ProjectRole | None:
    return await pj_roles_repositories.get_project_role(
        filters={"project_id": project_id, "slug": slug}
    )


##########################################################
# update project role permissions
##########################################################


async def update_project_role_permissions(
    role: ProjectRole, permissions: list[str]
) -> ProjectRole:
    if role.is_admin:
        raise ex.NonEditableRoleError("Cannot edit permissions in an admin role")

    # Check if new permissions have view_story
    view_story_is_deleted = False
    if role.permissions:
        view_story_is_deleted = (
            await stories_permissions.is_view_story_permission_deleted(
                old_permissions=role.permissions, new_permissions=permissions
            )
        )

    project_role_permissions = (
        await pj_roles_repositories.update_project_role_permissions(
            role=role,
            values={"permissions": permissions},
        )
    )

    await pj_roles_events.emit_event_when_project_role_permissions_are_updated(
        role=role
    )

    # Unassign stories for user if the new permissions don't have view_story
    if view_story_is_deleted:
        await story_assignments_repositories.delete_stories_assignments(
            filters={"role_id": role.id}
        )

    return project_role_permissions

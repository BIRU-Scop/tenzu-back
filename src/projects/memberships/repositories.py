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


from memberships.repositories import (  # noqa
    list_memberships,
    get_membership,
    exists_membership,
    update_membership,
    delete_membership,
    has_other_owner_memberships,
    list_members,
    list_roles,
    get_role,
    update_role,
)
from memberships.services import exceptions as ex
from projects.memberships.models import ProjectMembership, ProjectRole
from projects.projects.models import Project
from users.models import User
from workspaces.memberships.models import WorkspaceMembership


##########################################################
# create project membership
##########################################################


async def create_project_membership(
    user: User, project: Project, role: ProjectRole
) -> ProjectMembership:
    if project.id != role.project_id:
        raise ex.MembershipWithRoleThatDoNotBelong(
            "Can't create membership using a role not belonging to the given project"
        )
    if not await exists_membership(
        WorkspaceMembership,
        filters={
            "workspace_id": project.workspace_id,
            "user_id": user.id,
        },
    ):
        raise ex.NoRelativeWorkspaceMembershipsError(
            "Can't create project membership when user is not member of the relative workspace"
        )
    return await ProjectMembership.objects.acreate(
        user=user, project=project, role=role
    )


##########################################################
# create project role
##########################################################


async def create_project_role(
    name: str,
    permissions: list[str],
    project: Project,
    order: int | None = None,
) -> ProjectRole:
    return await ProjectRole.objects.acreate(
        name=name,
        permissions=permissions,
        project=project,
        order=order,
        is_owner=False,
        editable=True,
    )


async def bulk_create_project_roles(roles: list[ProjectRole]) -> list[ProjectRole]:
    return await ProjectRole.objects.abulk_create(roles)

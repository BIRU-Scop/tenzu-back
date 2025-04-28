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

from django.db.models import QuerySet

from memberships.repositories import (  # noqa
    delete_membership,
    exists_membership,
    get_membership,
    get_role,
    has_other_owner_memberships,
    list_members,
    list_memberships,
    list_roles,
    only_owner_collective_queryset,
    update_membership,
    update_role,
)
from memberships.repositories import (
    only_member_queryset as _only_member_queryset,
)
from memberships.services import exceptions as ex
from projects.memberships.models import ProjectMembership, ProjectRole
from projects.projects.models import Project
from projects.projects.repositories import ProjectFilters
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
        raise ex.NoRelatedWorkspaceMembershipsError(
            "Can't create project membership when user is not member of the related workspace"
        )
    return await ProjectMembership.objects.acreate(
        user=user, project=project, role=role
    )


##########################################################
# misc membership
##########################################################


def only_project_member_queryset(
    user: User,
    excludes: ProjectFilters = {},
) -> QuerySet[Project]:
    return _only_member_queryset(Project, user).exclude(**excludes)


##########################################################
# create project role
##########################################################


async def create_project_role(
    name: str,
    permissions: list[str],
    project_id: UUID,
) -> ProjectRole:
    return await ProjectRole.objects.acreate(
        name=name,
        permissions=permissions,
        project_id=project_id,
        is_owner=False,
        editable=True,
    )


async def bulk_create_project_roles(roles: list[ProjectRole]) -> list[ProjectRole]:
    return await ProjectRole.objects.abulk_create(roles)


##########################################################
# delete project role
##########################################################


async def delete_project_role(role: ProjectRole) -> int:
    count, _ = await role.adelete()
    return count


##########################################################
# misc project role
##########################################################


async def move_project_role_of_related(
    role: ProjectRole, target_role: ProjectRole
) -> None:
    if role.project_id != target_role.project_id:
        raise ex.RoleWithTargetThatDoNotBelong(
            "role and target role must be from the same project"
        )
    await role.memberships.aupdate(role=target_role)
    await role.invitations.aupdate(role=target_role)

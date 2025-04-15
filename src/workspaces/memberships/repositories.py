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
from permissions.choices import WorkspacePermissions

from users.models import User
from memberships.services import exceptions as ex
from workspaces.memberships.models import WorkspaceMembership, WorkspaceRole
from workspaces.workspaces.models import Workspace


##########################################################
# create workspace membership
##########################################################


async def create_workspace_membership(
    user: User, workspace: Workspace, role: WorkspaceRole
) -> WorkspaceMembership:
    if workspace.id != role.workspace_id:
        raise ex.MembershipWithRoleThatDoNotBelong(
            "Can't create membership using a role not belonging to the given workspace"
        )
    return await WorkspaceMembership.objects.acreate(
        user=user, workspace=workspace, role=role
    )


##########################################################
# create workspace role
##########################################################


async def bulk_create_workspace_default_roles(workspace) -> list[WorkspaceRole]:
    """
    Order of returned object is important for calling functions
    """
    return await WorkspaceRole.objects.abulk_create(
        [
            WorkspaceRole(
                workspace=workspace,
                name="Owner",
                slug="owner",
                order=1,
                editable=False,
                is_owner=True,
                permissions=list(WorkspacePermissions.values),
            ),
            WorkspaceRole(
                workspace=workspace,
                name="Admin",
                slug="admin",
                order=2,
                editable=False,
                is_owner=False,
                permissions=[
                    WorkspacePermissions.CREATE_MODIFY_MEMBER.value,
                    WorkspacePermissions.DELETE_MEMBER.value,
                    WorkspacePermissions.MODIFY_WORKSPACE.value,
                    WorkspacePermissions.CREATE_PROJECT.value,
                ],
            ),
            WorkspaceRole(
                workspace=workspace,
                name="Member",
                slug="member",
                order=3,
                editable=False,
                is_owner=False,
                permissions=[
                    WorkspacePermissions.CREATE_PROJECT.value,
                ],
            ),
            WorkspaceRole(
                workspace=workspace,
                name="Readonly-member",
                slug="readonly-member",
                order=4,
                editable=False,
                is_owner=False,
                permissions=[],
            ),
        ]
    )

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

import uuid

import pytest

from memberships.services import exceptions as ex
from permissions import choices
from permissions.choices import WorkspacePermissions
from tests.utils import factories as f
from workspaces.memberships import repositories
from workspaces.memberships.models import WorkspaceMembership, WorkspaceRole
from workspaces.workspaces.models import Workspace
from workspaces.workspaces.repositories import PROJECT_PREFETCH

pytestmark = pytest.mark.django_db


##########################################################
# create_workspace_memberhip
##########################################################


async def test_create_workspace_membership():
    user = await f.create_user()
    workspace = await f.create_workspace()
    role = await f.create_workspace_role(workspace=workspace)
    membership = await repositories.create_workspace_membership(
        user=user, workspace=workspace, role=role
    )
    memberships = [m async for m in workspace.memberships.all()]
    assert membership in memberships


async def test_create_workspace_membership_error_not_belong():
    user = await f.create_user()
    workspace = await f.create_workspace()
    other_workspace = await f.create_workspace()
    role = await f.create_workspace_role(workspace=workspace)
    with pytest.raises(ex.MembershipWithRoleThatDoNotBelong):
        await repositories.create_workspace_membership(
            user=user, workspace=other_workspace, role=role
        )


##########################################################
# list_workspaces_memberships
##########################################################


async def test_list_workspace_memberships():
    owner = await f.create_user()
    user1 = await f.create_user()
    user2 = await f.create_user()
    workspace = await f.create_workspace(created_by=owner)
    role = await f.create_workspace_role(workspace=workspace)
    await repositories.create_workspace_membership(
        user=user1, workspace=workspace, role=role
    )
    await repositories.create_workspace_membership(
        user=user2, workspace=workspace, role=role
    )

    memberships = await repositories.list_memberships(
        WorkspaceMembership,
        filters={"workspace_id": workspace.id},
    )
    assert len(memberships) == 3  # 2 explicitly created + owner membership


##########################################################
# get_workspace_membership
##########################################################


async def test_get_workspace_membership():
    user = await f.create_user()
    workspace = await f.create_workspace(created_by=user)

    membership = await repositories.get_membership(
        WorkspaceMembership,
        filters={"user_id": user.id, "workspace_id": workspace.id},
        select_related=["workspace", "user"],
    )
    assert membership.workspace == workspace
    assert membership.user == user

    membership = await repositories.get_membership(
        WorkspaceMembership,
        filters={
            "id": membership.id,
            "role__permissions__contains": [
                WorkspacePermissions.DELETE_WORKSPACE.value
            ],
        },
        select_related=["workspace", "user"],
    )
    assert membership.workspace == workspace
    assert membership.user == user

    membership = await repositories.get_membership(
        WorkspaceMembership,
        filters={"user__username": user.username},
        select_related=["workspace", "user"],
    )
    assert membership.workspace == workspace
    assert membership.user == user


async def test_get_workspace_membership_doesnotexist():
    with pytest.raises(WorkspaceMembership.DoesNotExist):
        await repositories.get_membership(
            WorkspaceMembership,
            filters={"user_id": uuid.uuid1(), "workspace_id": uuid.uuid1()},
        )


##########################################################
# update workspace membership
##########################################################


async def test_update_workspace_membership():
    user = await f.create_user()
    workspace = await f.create_workspace()
    role = await f.create_workspace_role(workspace=workspace)
    membership = await repositories.create_workspace_membership(
        user=user, workspace=workspace, role=role
    )

    new_role = await f.create_workspace_role(workspace=workspace)
    updated_membership = await repositories.update_membership(
        membership=membership, values={"role": new_role}
    )
    assert updated_membership.role == new_role


##########################################################
# delete workspace memberships
##########################################################


async def test_delete_workspace_membership() -> None:
    user = await f.create_user()
    member = await f.create_user()
    workspace = await f.create_workspace(created_by=user)
    role = await workspace.roles.afirst()
    membership = await f.create_workspace_membership(
        workspace=workspace, user=member, role=role
    )
    deleted = await repositories.delete_membership(membership)
    assert deleted == 1
    memberships = [m async for m in workspace.memberships.all()]
    assert len(memberships) == 1


##########################################################
# misc - has_other_owner_workspace_memberships
##########################################################


async def test_has_other_owner_workspace_memberships():
    user = await f.create_user()
    user2 = await f.create_user()
    workspace = await f.create_workspace()
    await f.create_workspace()
    owner_membership = await workspace.memberships.select_related("role").aget()
    role = await f.create_workspace_role(workspace=workspace)

    assert not await repositories.has_other_owner_memberships(owner_membership)

    await repositories.create_workspace_membership(
        user=user, workspace=workspace, role=role
    )
    assert not await repositories.has_other_owner_memberships(owner_membership)

    await repositories.create_workspace_membership(
        user=user2, workspace=workspace, role=owner_membership.role
    )
    assert await repositories.has_other_owner_memberships(owner_membership)


##########################################################
# misc - list_workspace_members
##########################################################


async def test_list_workspace_members():
    owner = await f.create_user()
    user1 = await f.create_user()
    user2 = await f.create_user()
    workspace = await f.create_workspace(created_by=owner)
    role = await workspace.roles.afirst()
    await repositories.create_workspace_membership(
        user=user1, workspace=workspace, role=role
    )
    await repositories.create_workspace_membership(
        user=user2, workspace=workspace, role=role
    )

    list_ws_members = await repositories.list_members(reference_object=workspace)
    assert len(list_ws_members) == 3


##########################################################
# misc - only_workspace_member_queryset
##########################################################


async def test_list_workspaces_user_only_member(project_template):
    user = await f.create_user()
    other_user = await f.create_user()
    # user only ws member with projects
    ws1 = await f.create_workspace(created_by=user)
    pj1_ws1 = await f.create_project(
        template=project_template, created_by=user, workspace=ws1
    )
    pj2_ws1 = await f.create_project(
        template=project_template, created_by=user, workspace=ws1
    )
    # user only ws member with projects
    ws2 = await f.create_workspace(created_by=user)
    pj1_ws2 = await f.create_project(
        template=project_template, created_by=user, workspace=ws2
    )
    # user only ws member without projects
    ws3 = await f.create_workspace(created_by=user)
    # user owner not only ws member
    ws4 = await f.create_workspace(created_by=user)
    await f.create_workspace_membership(user=other_user, workspace=ws4)
    # user not owner not only ws member
    ws5 = await f.create_workspace(created_by=other_user)
    await f.create_workspace_membership(user=user, workspace=ws5)
    # user not member
    ws6 = await f.create_workspace(created_by=other_user)

    ws_list = [
        ws
        async for ws in repositories.only_workspace_member_queryset(
            user, prefetch_related=[PROJECT_PREFETCH]
        )
    ]

    assert len(ws_list) == 3
    assert ws_list[0].name == ws1.name
    assert ws_list[1].name == ws2.name
    assert ws_list[2].name == ws3.name
    # assert prefetch order
    assert [pj.name for pj in ws_list[0].projects.all()] == [pj2_ws1.name, pj1_ws1.name]
    assert [pj.name for pj in ws_list[1].projects.all()] == [pj1_ws2.name]


##########################################################
# misc - only_owner_collective_queryset
##########################################################


async def test_list_projects_user_only_owner_but_not_only_member(project_template):
    user = await f.create_user()
    other_user = await f.create_user()
    # user only ws member
    await f.create_workspace(created_by=user)
    await f.create_workspace(created_by=user)

    # user only ws owner but not only member
    ws1 = await f.create_workspace(created_by=user)
    await f.create_workspace_membership(user=other_user, workspace=ws1)
    # user not only ws owner
    ws2 = await f.create_workspace(created_by=user)
    owner_role = await ws2.roles.aget(is_owner=True)
    await f.create_workspace_membership(user=other_user, workspace=ws2, role=owner_role)

    # user not member
    await f.create_workspace(created_by=other_user)
    # user not owner
    ws3 = await f.create_workspace(created_by=other_user)
    await f.create_workspace_membership(user=user, workspace=ws3)

    ws_list = [
        ws async for ws in repositories.only_owner_collective_queryset(Workspace, user)
    ]

    assert len(ws_list) == 1
    assert ws_list[0].name == ws1.name


##########################################################
# create workspace role
##########################################################


async def test_bulk_create_workspace_default_roles():
    user = await f.create_user()
    workspace = f.build_workspace(
        created_by=user
    )  # don't use create to prevent creation of default role and memberships
    await workspace.asave()
    workspace_roles_res = await repositories.bulk_create_workspace_default_roles(
        workspace
    )
    assert len(workspace_roles_res) == 4
    assert sum(1 for role in workspace_roles_res if role.is_owner) == 1
    assert not any(role.editable for role in workspace_roles_res)
    assert all(role.workspace == workspace for role in workspace_roles_res)


##########################################################
# list_workspace_roles
##########################################################


async def test_list_workspace_roles():
    workspace = await f.create_workspace()
    res = await repositories.list_roles(
        WorkspaceRole, filters={"workspace_id": workspace.id}
    )
    assert len(res) == 4  # factory default
    assert res[0].is_owner != res[1].is_owner


##########################################################
# get_workspace_role
##########################################################


async def test_get_workspace_role_return_role():
    workspace = await f.create_workspace()
    role = await f.create_workspace_role(
        name="Role test",
        slug="role-test",
        permissions=choices.WorkspacePermissions.choices,
        is_owner=True,
        workspace=workspace,
    )
    assert (
        await repositories.get_role(
            WorkspaceRole, filters={"workspace_id": workspace.id, "slug": "role-test"}
        )
        == role
    )


async def test_get_workspace_role_return_doesnotexist():
    workspace = await f.create_workspace()
    with pytest.raises(WorkspaceRole.DoesNotExist):
        await repositories.get_role(
            WorkspaceRole,
            filters={"workspace_id": workspace.id, "slug": "role-not-exist"},
        )


async def test_get_workspace_role_for_user_owner():
    user = await f.create_user()
    workspace = await f.create_workspace(created_by=user)
    role = await workspace.roles.aget(is_owner=True)

    assert (
        await repositories.get_role(
            WorkspaceRole,
            filters={"memberships__user_id": user.id, "workspace_id": workspace.id},
        )
        == role
    )


async def test_get_workspace_role_for_user_member():
    user = await f.create_user()
    workspace = await f.create_workspace()
    role = await f.create_workspace_role(workspace=workspace)
    await repositories.create_workspace_membership(
        user=user, workspace=workspace, role=role
    )

    assert (
        await repositories.get_role(
            WorkspaceRole,
            filters={"memberships__user_id": user.id, "workspace_id": workspace.id},
        )
        == role
    )


async def test_get_workspace_role_for_user_doesnotexist():
    user = await f.create_user()
    workspace = await f.create_workspace()

    with pytest.raises(WorkspaceRole.DoesNotExist):
        await repositories.get_role(
            WorkspaceRole,
            filters={"memberships__user_id": user.id, "workspace_id": workspace.id},
        )


##########################################################
# update workspace role
##########################################################


async def test_update_workspace_role():
    role = await f.create_workspace_role()
    updated_role = await repositories.update_role(
        role=role,
        values={"permissions": [WorkspacePermissions.MODIFY_WORKSPACE.value]},
    )
    assert WorkspacePermissions.MODIFY_WORKSPACE.value in updated_role.permissions

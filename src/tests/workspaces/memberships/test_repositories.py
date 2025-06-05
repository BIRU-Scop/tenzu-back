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


import pytest

from memberships.services import exceptions as ex
from permissions import choices
from permissions.choices import WorkspacePermissions
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID
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
    await workspace.arefresh_from_db(fields=["memberships"])
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


async def test_list_workspace_memberships_total_projects(project_template):
    owner = await f.create_user()
    user1 = await f.create_user()
    workspace = await f.create_workspace(created_by=owner)
    role = await workspace.roles.aget(slug="member")
    await f.create_workspace_membership(user=user1, workspace=workspace, role=role)
    await f.create_project(project_template, workspace=workspace, created_by=owner)
    project = await f.create_project(
        project_template, workspace=workspace, created_by=owner
    )
    role = await project.roles.aget(slug="member")
    await f.create_project_membership(user=user1, project=project, role=role)

    memberships = await repositories.list_memberships(
        WorkspaceMembership,
        filters={"workspace_id": workspace.id},
        annotations={
            "total_projects_is_member": repositories.TOTAL_PROJECTS_IS_MEMBER_ANNOTATION
        },
    )
    assert len(memberships) == 2  # user1 + owner
    assert memberships[0].total_projects_is_member == 2
    assert memberships[1].total_projects_is_member == 1


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


async def test_get_workspace_membership_total_projects(project_template):
    user = await f.create_user()
    workspace = await f.create_workspace(created_by=user)
    await f.create_project(project_template, workspace=workspace, created_by=user)
    await f.create_project(project_template, workspace=workspace, created_by=user)

    membership = await repositories.get_membership(
        WorkspaceMembership,
        filters={"user_id": user.id, "workspace_id": workspace.id},
        select_related=["workspace", "user"],
        annotations={
            "total_projects_is_member": repositories.TOTAL_PROJECTS_IS_MEMBER_ANNOTATION
        },
    )
    assert membership.workspace == workspace
    assert membership.user == user
    assert membership.total_projects_is_member == 2


async def test_get_workspace_membership_doesnotexist():
    with pytest.raises(WorkspaceMembership.DoesNotExist):
        await repositories.get_membership(
            WorkspaceMembership,
            filters={"user_id": NOT_EXISTING_UUID, "workspace_id": NOT_EXISTING_UUID},
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


async def test_bulk_update_or_create_memberships():
    workspace = await f.create_workspace()
    role = await f.create_workspace_role(workspace=workspace)
    owner_role = await workspace.roles.aget(is_owner=True)

    user = await f.create_user()
    member_membership = await repositories.create_workspace_membership(
        user=user, workspace=workspace, role=role
    )
    user = await f.create_user()
    owner_membership = await repositories.create_workspace_membership(
        user=user, workspace=workspace, role=owner_role
    )
    user = await f.create_user()

    new_memberships = [
        WorkspaceMembership(
            user=member_membership.user, workspace=workspace, role=owner_role
        ),
        WorkspaceMembership(
            user=owner_membership.user, workspace=workspace, role=owner_role
        ),
        WorkspaceMembership(user=user, workspace=workspace, role=owner_role),
    ]

    assert not await user.workspace_memberships.aexists()
    updated_memberships = await repositories.bulk_update_or_create_memberships(
        new_memberships
    )
    assert len(updated_memberships) == 3
    assert all(
        membership.role_id == owner_role.id for membership in updated_memberships
    )
    assert await user.workspace_memberships.aexists()


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
    deleted = await repositories.delete_memberships(
        WorkspaceMembership, {"id": membership.id}
    )
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
# misc - workspace_member_projects_list
##########################################################


async def test_workspace_member_projects_list(project_template):
    user = await f.create_user()
    other_user = await f.create_user()
    ws1 = await f.create_workspace(created_by=user)
    owner_membership = list(ws1.memberships.all())[0]
    await f.create_project(template=project_template, created_by=user, workspace=ws1)
    await f.create_project(template=project_template, created_by=user, workspace=ws1)
    await f.create_project_membership(user=user, project__workspace=ws1)
    await f.create_project_membership(user=other_user, project__workspace=ws1)

    ws2 = await f.create_workspace(created_by=other_user)
    await f.create_project(template=project_template, created_by=user, workspace=ws2)
    await f.create_project_membership(user=user, project__workspace=ws2)

    ws_list = await repositories.workspace_member_projects_list(owner_membership)

    assert len(ws_list) == 3


##########################################################
# misc - only_owner_queryset
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
        ws
        async for ws in repositories.only_owner_queryset(
            Workspace, user, is_collective=True
        )
    ]
    assert len(ws_list) == 1
    assert ws_list[0].name == ws1.name

    ws_list = [
        ws
        async for ws in repositories.only_owner_queryset(
            Workspace, user, is_collective=False
        )
    ]
    assert len(ws_list) == 3


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
    assert len(res) == 4
    assert sum(1 for role in res if role.is_owner) == 1
    assert all(not hasattr(role, "total_members") for role in res)
    res = await repositories.list_roles(
        WorkspaceRole, filters={"workspace_id": workspace.id}, get_total_members=True
    )
    assert len(res) == 4
    assert res[0].total_members == 1
    assert all(role.total_members == 0 for role in res[1:])


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

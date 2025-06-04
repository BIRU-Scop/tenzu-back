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
from operator import attrgetter

import pytest

from memberships.choices import InvitationStatus
from permissions import choices
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db


##########################################################
# LIST /workspaces/<id>/memberships
##########################################################


async def test_list_workspace_memberships(
    project_template,
    client,
):
    workspace = await f.create_workspace()

    general_member_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[],
        is_owner=False,
    )

    pj_member = await f.create_user()
    pj_member2 = await f.create_user()
    await f.create_workspace_membership(
        user=pj_member, workspace=workspace, role=general_member_role
    )
    await f.create_workspace_membership(
        user=pj_member2, workspace=workspace, role=general_member_role
    )
    await f.create_project(project_template, workspace=workspace)
    project = await f.create_project(project_template, workspace=workspace)
    role = await project.roles.aget(slug="member")
    await f.create_project_membership(user=pj_member2, project=project, role=role)

    client.login(pj_member)

    response = await client.get(f"/workspaces/{workspace.b64id}/memberships")
    assert response.status_code == 200, response.data
    res = response.json()
    assert len(res) == 3  # 2 explicitly created + owner membership
    assert res[0]["totalProjectsIsMember"] == 2
    assert res[1]["totalProjectsIsMember"] == 0
    assert res[2]["totalProjectsIsMember"] == 1


async def test_list_workspace_memberships_wrong_id(
    client,
):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{NOT_EXISTING_B64ID}/memberships")
    assert response.status_code == 404, response.data


async def test_list_workspace_memberships_not_a_member(
    client,
):
    workspace = await f.create_workspace()
    not_a_member = await f.create_user()

    client.login(not_a_member)
    response = await client.get(f"/workspaces/{workspace.b64id}/memberships")
    assert response.status_code == 403, response.data

    # even invitee can't see members
    general_admin_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=choices.WorkspacePermissions.values,
        is_owner=False,
    )
    await f.create_workspace_invitation(
        email=not_a_member.email,
        user=not_a_member,
        workspace=workspace,
        role=general_admin_role,
        status=InvitationStatus.PENDING,
    )
    response = await client.get(f"/workspaces/{workspace.b64id}/memberships")
    assert response.status_code == 403, response.data


##########################################################
# PATCH /workspaces/memberships/<id>
##########################################################


async def test_update_workspace_membership_role_membership_not_exist(
    client,
):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    member_role = next(filter(lambda role: role.slug == "member", roles))

    client.login(workspace.created_by)
    data = {"role_id": member_role.b64id}
    response = await client.patch(
        f"workspaces/memberships/{NOT_EXISTING_B64ID}", json=data
    )
    assert response.status_code == 404, response.data


async def test_update_workspace_membership_role_user_without_permission(
    client,
):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    member_role = next(filter(lambda role: role.slug == "member", roles))
    user1 = await f.create_user()
    user2 = await f.create_user()
    readonlymember_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[],
        is_owner=False,
    )
    membership = await f.create_workspace_membership(
        user=user2, workspace=workspace, role=readonlymember_role
    )

    client.login(user1)
    data = {"role_id": member_role.b64id}
    response = await client.patch(
        f"/workspaces/memberships/{membership.b64id}", json=data
    )
    assert response.status_code == 403, response.data

    await f.create_workspace_membership(
        user=user1, workspace=workspace, role=readonlymember_role
    )
    response = await client.patch(
        f"/workspaces/memberships/{membership.b64id}", json=data
    )
    assert response.status_code == 403, response.data


async def test_update_workspace_membership_role_ok(
    project_template,
    client,
):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    member_role = next(filter(lambda role: role.slug == "member", roles))
    user1 = await f.create_user()
    user2 = await f.create_user()
    general_admin_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[choices.WorkspacePermissions.CREATE_MODIFY_MEMBER.value],
        is_owner=False,
    )
    await f.create_workspace_membership(
        user=user1, workspace=workspace, role=general_admin_role
    )
    membership = await f.create_workspace_membership(
        user=user2, workspace=workspace, role=general_admin_role
    )
    await f.create_project(project_template, workspace=workspace)
    project = await f.create_project(project_template, workspace=workspace)
    role = await project.roles.aget(slug="member")
    await f.create_project_membership(user=user2, project=project, role=role)

    client.login(workspace.created_by)
    data = {"role_id": member_role.b64id}
    response = await client.patch(
        f"workspaces/memberships/{membership.b64id}", json=data
    )
    assert response.status_code == 200, response.data
    assert response.json()["totalProjectsIsMember"] == 1

    client.login(user1)
    response = await client.patch(
        f"workspaces/memberships/{membership.b64id}", json=data
    )
    assert response.status_code == 200, response.data
    assert response.json()["totalProjectsIsMember"] == 1


async def test_update_workspace_membership_role_owner_and_not_owner(
    client,
):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    owner_role = next(filter(attrgetter("is_owner"), roles))
    member_role = next(filter(lambda role: role.slug == "member", roles))
    user1 = await f.create_user()
    user2 = await f.create_user()
    general_admin_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[choices.WorkspacePermissions.CREATE_MODIFY_MEMBER.value],
        is_owner=False,
    )
    await f.create_workspace_membership(
        user=user1, workspace=workspace, role=general_admin_role
    )
    membership = await f.create_workspace_membership(
        user=user2, workspace=workspace, role=general_admin_role
    )

    client.login(user1)
    # change role to owner
    data = {"role_id": owner_role.b64id}
    response = await client.patch(
        f"/workspaces/memberships/{membership.b64id}", json=data
    )
    assert response.status_code == 403, response.data
    # change role of owner
    owner_membership = list(workspace.memberships.all())[0]
    data = {"role_id": member_role.b64id}
    response = await client.patch(
        f"/workspaces/memberships/{owner_membership.b64id}", json=data
    )
    assert response.status_code == 403, response.data


async def test_update_workspace_membership_role_owner_and_owner(
    client,
):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    owner_role = next(filter(attrgetter("is_owner"), roles))
    member_role = next(filter(lambda role: role.slug == "member", roles))
    user = await f.create_user()
    general_member_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[],
        is_owner=False,
    )
    membership = await f.create_workspace_membership(
        user=user, workspace=workspace, role=general_member_role
    )

    client.login(workspace.created_by)
    # change role to owner
    data = {"role_id": owner_role.b64id}
    response = await client.patch(
        f"/workspaces/memberships/{membership.b64id}", json=data
    )
    assert response.status_code == 200, response.data
    # change role of owner
    data = {"role_id": member_role.b64id}
    response = await client.patch(
        f"/workspaces/memberships/{membership.b64id}", json=data
    )
    assert response.status_code == 200, response.data


##########################################################
# DELETE /workspaces/memberships/<id>
##########################################################


async def test_delete_workspace_membership_not_exist(
    client,
):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.delete(f"/workspaces/memberships/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data


async def test_delete_workspace_membership_without_permissions(
    client,
):
    workspace = await f.create_workspace()
    user1 = await f.create_user()
    user2 = await f.create_user()
    general_member_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[],
        is_owner=False,
    )
    await f.create_workspace_membership(
        user=user1, workspace=workspace, role=general_member_role
    )
    membership = await f.create_workspace_membership(
        user=user2, workspace=workspace, role=general_member_role
    )

    client.login(user1)
    response = await client.delete(f"/workspaces/memberships/{membership.b64id}")
    assert response.status_code == 403, response.data


@pytest.mark.django_db(transaction=True)
async def test_delete_workspace_membership_role_ok(
    client,
):
    workspace = await f.create_workspace()
    user1 = await f.create_user()
    user2 = await f.create_user()
    general_admin_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[choices.WorkspacePermissions.DELETE_MEMBER.value],
        is_owner=False,
    )
    await f.create_workspace_membership(
        user=user1, workspace=workspace, role=general_admin_role
    )
    membership = await f.create_workspace_membership(
        user=user2, workspace=workspace, role=general_admin_role
    )

    client.login(user1)
    response = await client.delete(f"/workspaces/memberships/{membership.b64id}")
    assert response.status_code == 204, response.data


async def test_delete_workspace_membership_only_owner_bad_successor(client):
    workspace = await f.create_workspace()
    owner_membership = list(workspace.memberships.all())[0]

    client.login(workspace.created_by)
    response = await client.delete(f"/workspaces/memberships/{owner_membership.b64id}")
    assert response.status_code == 400, response.data

    # invalid successor
    response = await client.delete(
        f"/workspaces/memberships/{owner_membership.b64id}?successorUserId={NOT_EXISTING_B64ID}"
    )
    assert response.status_code == 400, response.data

    # successor not in project
    user = await f.create_user()
    response = await client.delete(
        f"/workspaces/memberships/{owner_membership.b64id}?successorUserId={user.b64id}"
    )
    assert response.status_code == 400, response.data
    assert str(user.id) in response.data["error"]["msg"]

    # successor is deleted member
    response = await client.delete(
        f"/workspaces/memberships/{owner_membership.b64id}?successorUserId={owner_membership.user.b64id}"
    )
    assert response.status_code == 400, response.data


async def test_delete_workspace_membership_only_owner_ok_successor(client):
    workspace = await f.create_workspace()
    owner_membership = list(workspace.memberships.all())[0]
    other_membership = await f.create_workspace_membership(workspace=workspace)

    client.login(workspace.created_by)
    response = await client.delete(
        f"/workspaces/memberships/{owner_membership.b64id}?successorUserId={other_membership.user.b64id}"
    )
    assert response.status_code == 204, response.data
    await other_membership.arefresh_from_db()
    assert other_membership.role_id == owner_membership.role_id


async def test_delete_workspace_membership_not_owner(client, project_template):
    workspace = await f.create_workspace()
    owner_membership = list(workspace.memberships.all())[0]
    user = await f.create_user()
    general_admin_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[choices.WorkspacePermissions.DELETE_MEMBER.value],
        is_owner=False,
    )
    await f.create_workspace_membership(
        user=user, workspace=workspace, role=general_admin_role
    )

    client.login(user)
    # trying to delete ws owner
    response = await client.delete(f"/workspaces/memberships/{owner_membership.b64id}")
    assert response.status_code == 403, response.data

    # trying to delete owner of a project of the ws
    other_admin_user = await f.create_user()
    general_admin_membership = await f.create_workspace_membership(
        user=other_admin_user, workspace=workspace, role=general_admin_role
    )
    await f.create_project(
        project_template, created_by=other_admin_user, workspace=workspace
    )
    response = await client.delete(
        f"/workspaces/memberships/{general_admin_membership.b64id}"
    )
    assert response.status_code == 403, response.data


@pytest.mark.django_db(transaction=True)
async def test_delete_workspace_membership_role_owner_and_owner(
    client, project_template
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    owner_role = await workspace.roles.aget(is_owner=True)
    membership = await f.create_workspace_membership(
        user=user, workspace=workspace, role=owner_role
    )

    client.login(workspace.created_by)
    response = await client.delete(f"/workspaces/memberships/{membership.b64id}")
    assert response.status_code == 204, response.data

    # ok event if deleted member is only owner of some projects
    membership = await f.create_workspace_membership(
        user=user, workspace=workspace, role=owner_role
    )
    project_ws_owner_is_member = await f.create_project(
        project_template, workspace=workspace, created_by=user
    )
    general_role = await project_ws_owner_is_member.roles.filter(
        is_owner=False
    ).afirst()
    await f.create_project_membership(
        user=workspace.created_by, project=project_ws_owner_is_member, role=general_role
    )
    project_ws_owner_not_member = await f.create_project(
        project_template, workspace=workspace, created_by=user
    )
    general_role = await project_ws_owner_not_member.roles.filter(
        is_owner=False
    ).afirst()
    other_member = await f.create_user()
    await f.create_project_membership(
        user=other_member,
        project=project_ws_owner_not_member,
        role=general_role,
    )
    project_only_1_member = await f.create_project(
        project_template, workspace=workspace, created_by=user
    )
    response = await client.delete(f"/workspaces/memberships/{membership.b64id}")
    assert response.status_code == 204, response.data
    assert [m async for m in project_ws_owner_is_member.members.all()] == [
        workspace.created_by
    ]
    assert sorted(
        [m async for m in project_ws_owner_not_member.members.all()],
        key=attrgetter("id"),
    ) == [workspace.created_by, other_member]
    assert [m async for m in project_only_1_member.members.all()] == [
        workspace.created_by
    ]


async def test_delete_workspace_membership_self_member_request(
    client, project_template
):
    workspace = await f.create_workspace()
    member = await f.create_user()
    general_member_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[],
        is_owner=False,
    )
    membership = await f.create_workspace_membership(
        user=member, workspace=workspace, role=general_member_role
    )

    client.login(member)
    response = await client.delete(f"/workspaces/memberships/{membership.b64id}")
    assert response.status_code == 204, response.data

    # error if user existing project
    await f.create_project(project_template, workspace=workspace, created_by=member)

    membership = await f.create_workspace_membership(
        user=member, workspace=workspace, role=general_member_role
    )
    client.login(member)
    response = await client.delete(f"/workspaces/memberships/{membership.b64id}")
    assert response.status_code == 400, response.data


##########################################################
# LIST /workspaces/<id>/roles
##########################################################


async def test_list_workspace_roles(
    client,
):
    workspace = await f.create_workspace()

    general_member_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[],
        is_owner=False,
    )

    pj_member = await f.create_user()
    await f.create_workspace_membership(
        user=pj_member, workspace=workspace, role=general_member_role
    )

    client.login(pj_member)

    response = await client.get(f"/workspaces/{workspace.b64id}/roles")
    assert response.status_code == 200, response.data
    assert len(response.json()) == 5  # 4 factory default + newly created


async def test_list_workspace_roles_wrong_id(
    client,
):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{NOT_EXISTING_B64ID}/roles")
    assert response.status_code == 404, response.data


async def test_list_workspace_roles_not_a_member(
    client,
):
    workspace = await f.create_workspace()
    not_a_member = await f.create_user()

    client.login(not_a_member)
    response = await client.get(f"/workspaces/{workspace.b64id}/roles")
    assert response.status_code == 403, response.data

    # even invitee can't see members
    general_admin_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=choices.WorkspacePermissions.values,
        is_owner=False,
    )
    await f.create_workspace_invitation(
        email=not_a_member.email,
        user=not_a_member,
        workspace=workspace,
        role=general_admin_role,
        status=InvitationStatus.PENDING,
    )
    response = await client.get(f"/workspaces/{workspace.b64id}/roles")
    assert response.status_code == 403, response.data

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
from fastapi import status

from memberships.choices import InvitationStatus
from permissions import choices
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db


##########################################################
# LIST /workspaces/<id>/memberships
##########################################################


async def test_list_workspace_memberships(
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

    client.login(pj_member)

    response = await client.get(f"/workspaces/{workspace.b64id}/memberships")
    assert response.status_code == status.HTTP_200_OK, response.data
    assert len(response.json()) == 3  # 2 explicitly created + owner membership


async def test_list_workspace_memberships_wrong_id(
    client,
):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{NOT_EXISTING_B64ID}/memberships")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.data


async def test_list_workspace_memberships_not_a_member(
    client,
):
    workspace = await f.create_workspace()
    not_a_member = await f.create_user()

    client.login(not_a_member)
    response = await client.get(f"/workspaces/{workspace.b64id}/memberships")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data

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
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data


##########################################################
# PATCH /workspaces/<id>/memberships/<username>
##########################################################


async def test_update_workspace_membership_role_membership_not_exist(
    client,
):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    username = "not_exist"
    data = {"role_slug": "member"}
    response = await client.patch(
        f"workspaces/{workspace.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.data


async def test_update_workspace_membership_role_user_without_permission(
    client,
):
    workspace = await f.create_workspace()
    user1 = await f.create_user()
    user2 = await f.create_user()
    member_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[],
        is_owner=False,
    )
    await f.create_workspace_membership(
        user=user2, workspace=workspace, role=member_role
    )

    client.login(user1)
    username = user2.username
    data = {"role_slug": "member"}
    response = await client.patch(
        f"/workspaces/{workspace.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data

    await f.create_workspace_membership(
        user=user1, workspace=workspace, role=member_role
    )
    response = await client.patch(
        f"/workspaces/{workspace.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data


async def test_update_workspace_membership_role_ok(
    client,
):
    workspace = await f.create_workspace()
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
    await f.create_workspace_membership(
        user=user2, workspace=workspace, role=general_admin_role
    )

    client.login(workspace.created_by)
    data = {"role_slug": "member"}
    response = await client.patch(
        f"workspaces/{workspace.b64id}/memberships/{user2.username}", json=data
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    client.login(user1)
    response = await client.patch(
        f"workspaces/{workspace.b64id}/memberships/{user2.username}", json=data
    )
    assert response.status_code == status.HTTP_200_OK, response.data


async def test_update_workspace_membership_role_owner_and_not_owner(
    client,
):
    workspace = await f.create_workspace()
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
    await f.create_workspace_membership(
        user=user2, workspace=workspace, role=general_admin_role
    )

    client.login(user1)
    # change role to owner
    username = user2.username
    data = {"role_slug": "owner"}
    response = await client.patch(
        f"/workspaces/{workspace.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
    # change role of owner
    username = workspace.created_by.username
    data = {"role_slug": "member"}
    response = await client.patch(
        f"/workspaces/{workspace.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data


async def test_update_workspace_membership_role_owner_and_owner(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    general_member_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[],
        is_owner=False,
    )
    await f.create_workspace_membership(
        user=user, workspace=workspace, role=general_member_role
    )

    client.login(workspace.created_by)
    # change role to owner
    username = user.username
    data = {"role_slug": "owner"}
    response = await client.patch(
        f"/workspaces/{workspace.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    # change role of owner
    data = {"role_slug": "member"}
    response = await client.patch(
        f"/workspaces/{workspace.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_200_OK, response.data


##########################################################
# DELETE /workspaces/<id>/memberships/<username>
##########################################################


async def test_delete_workspace_membership_not_exist(
    client,
):
    workspace = await f.create_workspace()
    username = "not_exist"

    client.login(workspace.created_by)
    response = await client.delete(
        f"/workspaces/{workspace.b64id}/memberships/{username}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.data


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
    await f.create_workspace_membership(
        user=user2, workspace=workspace, role=general_member_role
    )

    client.login(user1)
    response = await client.delete(
        f"/workspaces/{workspace.b64id}/memberships/{user2.username}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data


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
    await f.create_workspace_membership(
        user=user2, workspace=workspace, role=general_admin_role
    )

    client.login(user1)
    response = await client.delete(
        f"/workspaces/{workspace.b64id}/memberships/{user2.username}"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.data


async def test_delete_workspace_membership_only_owner(
    client,
):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.delete(
        f"/workspaces/{workspace.b64id}/memberships/{workspace.created_by.username}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data


async def test_delete_workspace_membership_role_owner_and_not_owner(
    client,
):
    workspace = await f.create_workspace()
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
    response = await client.delete(
        f"/workspaces/{workspace.b64id}/memberships/{workspace.created_by.username}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data


async def test_delete_workspace_membership_role_owner_and_owner(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    owner_role = await workspace.roles.aget(is_owner=True)
    await f.create_workspace_membership(user=user, workspace=workspace, role=owner_role)

    client.login(workspace.created_by)
    response = await client.delete(
        f"/workspaces/{workspace.b64id}/memberships/{user.username}"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.data


async def test_delete_workspace_membership_self_request(
    client,
):
    workspace = await f.create_workspace()
    member = await f.create_user()
    general_member_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=[],
        is_owner=False,
    )
    await f.create_workspace_membership(
        user=member, workspace=workspace, role=general_member_role
    )

    client.login(member)
    response = await client.delete(
        f"/workspaces/{workspace.b64id}/memberships/{member.username}"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.data


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
    assert response.status_code == status.HTTP_200_OK, response.data
    assert len(response.json()) == 5  # 4 factory default + newly created


async def test_list_workspace_roles_wrong_id(
    client,
):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{NOT_EXISTING_B64ID}/roles")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.data


async def test_list_workspace_roles_not_a_member(
    client,
):
    workspace = await f.create_workspace()
    not_a_member = await f.create_user()

    client.login(not_a_member)
    response = await client.get(f"/workspaces/{workspace.b64id}/roles")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data

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
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data

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

from permissions.choices import WorkspacePermissions
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db


#############################################################
#  POST /workspaces/
#############################################################


async def test_create_workspace_being_anonymous(client):
    data = {
        "name": "WS test",
        "color": 1,
    }

    response = await client.post("/workspaces", json=data)
    assert response.status_code == 401, response.data


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
async def test_create_workspace_success(client):
    user = await f.create_user()
    data = {
        "name": "WS test",
        "color": 1,
    }

    client.login(user)
    response = await client.post("/workspaces", json=data)
    assert response.status_code == 200, response.data
    res = response.data
    assert res["userRole"]["isOwner"] is True
    assert res["userIsInvited"] is False
    assert res["userIsMember"] is True
    assert res["userCanCreateProjects"] is True
    assert res["totalProjects"] == 0


async def test_create_workspace_validation_error(client):
    user = await f.create_user()
    data = {
        "name": "My w0r#%&乕شspace",
        "color": 0,  # error
    }

    client.login(user)
    response = await client.post("/workspaces", json=data)
    assert response.status_code == 422, response.data


#############################################################
#  GET /workspaces/
#############################################################


async def test_list_workspaces_being_anonymous(client):
    response = await client.get("/workspaces")
    assert response.status_code == 401, response.data


async def test_list_workspaces_success_owner_no_project(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.get("/workspaces")
    assert response.status_code == 200, response.data
    res = response.data
    assert len(res) == 1
    assert res[0]["name"] == workspace.name
    assert res[0]["userIsInvited"] is False
    assert res[0]["userIsMember"] is True
    assert res[0]["userCanCreateProjects"] is True
    assert res[0]["userMemberProjects"] == []
    assert res[0]["userInvitedProjects"] == []


async def test_list_workspaces_success_owner_one_project(client, project_template):
    workspace = await f.create_workspace()
    project = await f.create_project(project_template, workspace=workspace)

    client.login(workspace.created_by)
    response = await client.get("/workspaces")
    assert response.status_code == 200, response.data
    res = response.data
    # assert len(res) == 1
    # assert res[0]["name"] == workspace.name
    # assert res[0]["userIsInvited"] is False
    # assert res[0]["userIsMember"] is True
    # assert res[0]["userCanCreateProjects"] is True
    # assert len(res[0]["userMemberProjects"]) == 1
    # assert res[0]["userMemberProjects"][0]["name"] == project.name
    # assert res[0]["userInvitedProjects"] == []


async def test_list_workspaces_success_ws_invitee(client):
    ws_invitation = await f.create_workspace_invitation()

    client.login(ws_invitation.user)
    response = await client.get("/workspaces")
    assert response.status_code == 200, response.data
    res = response.data
    # assert len(res) == 1
    # assert res[0]["name"] == ws_invitation.workspace.name
    # assert res[0]["userIsInvited"] is True
    # assert res[0]["userIsMember"] is False
    # assert res[0]["userCanCreateProjects"] is False
    # assert res[0]["userMemberProjects"] == []
    # assert res[0]["userInvitedProjects"] == []


async def test_list_workspaces_success_pj_invitee(client):
    pj_invitation = await f.create_project_invitation()

    client.login(pj_invitation.user)
    response = await client.get("/workspaces")
    assert response.status_code == 200, response.data
    res = response.data
    # assert len(res) == 1
    # assert res[0]["name"] == pj_invitation.project.workspace.name
    # assert res[0]["userIsInvited"] is False
    # assert res[0]["userIsMember"] is False
    # assert res[0]["userCanCreateProjects"] is False
    # assert res[0]["userMemberProjects"] == []
    # assert len(res[0]["userInvitedProjects"]) == 1
    # assert res[0]["userInvitedProjects"][0]["name"] == pj_invitation.project.name


#############################################################
#  GET /workspaces/<id>
#############################################################


async def test_get_workspace_success_owner(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 200, response.data
    res = response.data
    assert res["name"] == workspace.name
    assert res["userRole"]["isOwner"]
    assert res["userIsInvited"] is False
    assert res["userIsMember"] is True
    assert res["userCanCreateProjects"] is True
    assert res["totalProjects"] == 0


async def test_get_workspace_success_member(client):
    workspace = await f.create_workspace()
    ws_member = await f.create_user()
    await f.create_workspace_membership(user=ws_member, workspace=workspace)

    client.login(ws_member)
    response = await client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 200, response.data
    res = response.data
    assert res["name"] == workspace.name
    assert not res["userRole"]["isOwner"]
    assert res["userIsInvited"] is False
    assert res["userIsMember"] is True
    assert res["userCanCreateProjects"] is True
    assert res["totalProjects"] == 0


async def test_get_workspace_success_ws_invited(client):
    ws_invitation = await f.create_workspace_invitation()

    client.login(ws_invitation.user)
    response = await client.get(f"/workspaces/{ws_invitation.workspace.b64id}")
    assert response.status_code == 200, response.data
    res = response.data
    assert res["name"] == ws_invitation.workspace.name
    assert res["userRole"] is None
    assert res["userIsInvited"] is True
    assert res["userIsMember"] is False
    assert res["userCanCreateProjects"] is False
    assert res["totalProjects"] == 0


async def test_get_workspace_success_ws_invited_only_email(client):
    user = await f.create_user()
    ws_invitation = await f.create_workspace_invitation(user=None, email=user.email)

    client.login(user)
    response = await client.get(f"/workspaces/{ws_invitation.workspace.b64id}")
    assert response.status_code == 200, response.data
    res = response.data
    assert res["name"] == ws_invitation.workspace.name
    assert res["userRole"] is None
    assert res["userIsInvited"] is True
    assert res["userIsMember"] is False
    assert res["userCanCreateProjects"] is False
    assert res["totalProjects"] == 0


async def test_get_workspace_success_pj_invited(client):
    pj_invitation = await f.create_project_invitation()

    client.login(pj_invitation.user)
    response = await client.get(f"/workspaces/{pj_invitation.project.workspace.b64id}")
    assert response.status_code == 200, response.data
    res = response.data
    assert res["name"] == pj_invitation.project.workspace.name
    assert res["userRole"] is None
    assert res["userIsInvited"] is False
    assert res["userIsMember"] is False
    assert res["userCanCreateProjects"] is False
    assert res["totalProjects"] == 1


async def test_get_workspace_success_pj_invited_only_email(client):
    user = await f.create_user()
    pj_invitation = await f.create_project_invitation(user=None, email=user.email)

    client.login(user)
    response = await client.get(f"/workspaces/{pj_invitation.project.workspace.b64id}")
    assert response.status_code == 200, response.data
    res = response.data
    assert res["name"] == pj_invitation.project.workspace.name
    assert res["userRole"] is None
    assert res["userIsInvited"] is False
    assert res["userIsMember"] is False
    assert res["userCanCreateProjects"] is False
    assert res["totalProjects"] == 1


async def test_get_workspace_not_found_error_because_invalid_id(client):
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/workspaces/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data


async def test_get_workspace_forbidden_anonymous(client):
    workspace = await f.create_workspace()

    response = await client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 401, response.data


async def test_get_workspace_forbidden_because_there_is_no_relation(client):
    user = await f.create_user()
    workspace = await f.create_workspace()

    client.login(user)
    response = await client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 403, response.data


##########################################################
# PATCH /workspaces/<id>/
##########################################################


async def test_update_workspace_200_ok(client, project_template):
    workspace = await f.create_workspace()
    data = {"name": "New name"}

    client.login(workspace.created_by)
    response = await client.patch(f"/workspaces/{workspace.b64id}", json=data)
    assert response.status_code == 200, response.data
    updated_workspace = response.data
    assert updated_workspace["name"] == "New name"
    assert updated_workspace["userRole"]["isOwner"] is True
    assert updated_workspace["userIsInvited"] is False
    assert updated_workspace["userIsMember"] is True
    assert updated_workspace["userCanCreateProjects"] is True
    assert updated_workspace["totalProjects"] == 0

    ws_member = await f.create_user()
    general_member_role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.MODIFY_WORKSPACE.value],
        is_owner=False,
        workspace=workspace,
    )
    await f.create_workspace_membership(
        user=ws_member, workspace=workspace, role=general_member_role
    )
    await f.create_project(project_template, workspace=workspace)
    client.login(ws_member)
    response = await client.patch(f"/workspaces/{workspace.b64id}", json=data)
    assert response.status_code == 200, response.data
    updated_workspace = response.json()
    assert updated_workspace["name"] == "New name"
    assert updated_workspace["userRole"]["isOwner"] is False
    assert updated_workspace["userIsInvited"] is False
    assert updated_workspace["userIsMember"] is True
    assert updated_workspace["userCanCreateProjects"] is False
    assert updated_workspace["totalProjects"] == 1


async def test_update_workspace_403_forbidden_member_without_permissions(
    client,
):
    workspace = await f.create_workspace()
    general_member_role = await f.create_workspace_role(
        permissions=[],
        is_owner=False,
        workspace=workspace,
    )

    user = await f.create_user()
    await f.create_workspace_membership(
        user=user, workspace=workspace, role=general_member_role
    )

    data = {"name": "new name"}
    client.login(user)
    response = await client.patch(f"/workspaces/{workspace.b64id}", json=data)
    assert response.status_code == 403, response.data


async def test_update_workspace_403_forbidden_not_member(
    client,
):
    user = await f.create_user()
    workspace = await f.create_workspace()

    data = {"name": "new name"}
    client.login(user)
    response = await client.patch(f"/workspaces/{workspace.b64id}", json=data)
    assert response.status_code == 403, response.data


async def test_update_workspace_404_not_found_workspace_b64id(client):
    user = await f.create_user()
    data = {"name": "new name"}

    client.login(user)
    response = await client.patch(f"/workspaces/{NOT_EXISTING_B64ID}", json=data)
    assert response.status_code == 404, response.data


async def test_update_workspace_422_unprocessable_workspace_b64id(client):
    user = await f.create_user()
    data = {"name": "new name"}

    client.login(user)
    response = await client.patch(f"/workspaces/{INVALID_B64ID}", json=data)
    assert response.status_code == 422, response.data


#############################################################
#  DELETE /workspaces/<id>
#############################################################


async def test_delete_workspace_204_no_content_being_ws_owner(
    client,
):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.delete(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 204, response.data


async def test_delete_workspace_204_no_content_being_ws_member(
    client,
):
    workspace = await f.create_workspace()
    general_member_role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.DELETE_WORKSPACE.value],
        is_owner=False,
        workspace=workspace,
    )

    user = await f.create_user()
    await f.create_workspace_membership(
        user=user, workspace=workspace, role=general_member_role
    )
    client.login(user)
    response = await client.delete(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 204, response.data


async def test_delete_workspace_403_forbidden_member_without_permissions(
    client,
):
    workspace = await f.create_workspace()
    general_member_role = await f.create_workspace_role(
        permissions=[],
        is_owner=False,
        workspace=workspace,
    )

    user = await f.create_user()
    await f.create_workspace_membership(
        user=user, workspace=workspace, role=general_member_role
    )

    client.login(user)
    response = await client.delete(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 403, response.data


async def test_delete_workspace_403_forbidden_not_member(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()

    client.login(user)
    response = await client.delete(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 403, response.data


async def test_delete_workspace_not_found(client):
    user = await f.create_user()

    client.login(user)
    response = await client.delete(f"/workspaces/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data

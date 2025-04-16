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
#  POST /my/workspaces/
#############################################################


async def test_create_workspace_being_anonymous(client):
    data = {
        "name": "WS test",
        "color": 1,
    }

    response = await client.post("/workspaces", json=data)
    assert response.status_code == 401, response.data


async def test_create_workspace_success(client):
    user = await f.create_user()
    data = {
        "name": "WS test",
        "color": 1,
    }

    client.login(user)
    response = await client.post("/workspaces", json=data)
    assert response.status_code == 200, response.data


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
#  GET /my/workspaces/
#############################################################


async def test_my_workspaces_being_anonymous(client):
    response = await client.get("/my/workspaces")
    assert response.status_code == 401, response.data


async def test_my_workspaces_success(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.get("/my/workspaces")
    assert response.status_code == 200, response.data
    assert len(response.json()) == 1


#############################################################
#  GET /my/workspaces/<id>
#############################################################


async def test_my_workspace_being_anonymous(client):
    workspace = await f.create_workspace()

    response = await client.get(f"/my/workspaces/{workspace.b64id}")
    assert response.status_code == 401, response.data


async def test_my_workspace_success(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.get(f"/my/workspaces/{workspace.b64id}")
    assert response.status_code == 200, response.data
    assert response.json()["name"] == workspace.name


async def test_my_workspace_not_found_error_because_invalid_id(client):
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/my/workspaces/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data


async def test_my_workspace_not_found_error_because_there_is_no_relation(client):
    user = await f.create_user()
    workspace = await f.create_workspace()

    client.login(user)
    response = await client.get(f"/my/workspaces/{workspace.b64id}")
    assert response.status_code == 404, response.data


#############################################################
#  GET /workspaces/<id>
#############################################################


async def test_get_workspace_being_workspace_owner(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 200, response.data


async def test_get_workspace_200_ok_being_ws_member(client):
    workspace = await f.create_workspace()
    ws_member = await f.create_user()
    general_member_role = await f.create_workspace_role(
        permissions=[],
        is_owner=False,
        workspace=workspace,
    )
    await f.create_workspace_membership(
        user=ws_member, workspace=workspace, role=general_member_role
    )

    client.login(ws_member)
    response = await client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 200, response.data


async def test_get_workspace_200_ok_being_invited_user(
    client,
):
    user = await f.create_user()
    workspace = await f.create_workspace()
    await f.create_workspace_invitation(user=user, workspace=workspace)

    client.login(user)
    response = await client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 200, response.data


async def test_get_workspace_200_ok_being_inner_project_invited_user(
    client, project_template
):
    user = await f.create_user()
    project = await f.create_project(project_template)
    await f.create_project_invitation(user=user, project=project)

    client.login(user)
    response = await client.get(f"/workspaces/{project.workspace.b64id}")
    assert response.status_code == 200, response.data


async def test_get_workspace_403_forbidden_not_workspace_member(client):
    workspace = await f.create_workspace()

    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 403, response.data


async def test_get_workspace_being_anonymous(client):
    workspace = await f.create_workspace()

    response = await client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == 401, response.data


async def test_get_workspace_not_found_error(client):
    user = await f.create_user()

    client.login(user)
    response = await client.get(f"/workspaces/{NOT_EXISTING_B64ID}")
    assert response.status_code == 404, response.data


##########################################################
# PATCH /workspaces/<id>/
##########################################################


async def test_update_workspace_200_ok(client):
    workspace = await f.create_workspace()
    data = {"name": "New name"}

    client.login(workspace.created_by)
    response = await client.patch(f"/workspaces/{workspace.b64id}", json=data)
    assert response.status_code == 200, response.data
    updated_workspace = response.json()
    assert updated_workspace["name"] == "New name"

    ws_member = await f.create_user()
    general_member_role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.MODIFY_WORKSPACE.value],
        is_owner=False,
        workspace=workspace,
    )
    await f.create_workspace_membership(
        user=ws_member, workspace=workspace, role=general_member_role
    )
    client.login(ws_member)
    response = await client.patch(f"/workspaces/{workspace.b64id}", json=data)
    assert response.status_code == 200, response.data


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

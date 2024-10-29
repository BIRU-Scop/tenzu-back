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

from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db(transaction=True)


#############################################################
#  POST /my/workspaces/
#############################################################


async def test_create_workspace_success(client):
    user = await f.create_user()
    data = {
        "name": "WS test",
        "color": 1,
    }

    client.login(user)
    response = client.post("/workspaces", json=data)
    assert response.status_code == status.HTTP_200_OK, response.text


async def test_create_workspace_validation_error(client):
    user = await f.create_user()
    data = {
        "name": "My w0r#%&乕شspace",
        "color": 0,  # error
    }

    client.login(user)
    response = client.post("/workspaces", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


#############################################################
#  GET /my/workspaces/
#############################################################


async def test_my_workspaces_being_anonymous(client):
    response = client.get("/my/workspaces")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_my_workspaces_success(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = client.get("/my/workspaces")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert len(response.json()) == 1


#############################################################
#  GET /my/workspaces/<id>
#############################################################


async def test_my_workspace_being_anonymous(client):
    workspace = await f.create_workspace()

    response = client.get(f"/my/workspaces/{workspace.b64id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_my_workspace_success(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = client.get(f"/my/workspaces/{workspace.b64id}")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["name"] == workspace.name


async def test_my_workspace_not_found_error_because_invalid_id(client):
    user = await f.create_user()
    non_existent_id = "xxxxxxxxxxxxxxxxxxxxxx"

    client.login(user)
    response = client.get(f"/my/workspaces/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_my_workspace_not_found_error_because_there_is_no_relation(client):
    user = await f.create_user()
    workspace = await f.create_workspace()

    client.login(user)
    response = client.get(f"/my/workspaces/{workspace.b64id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


#############################################################
#  GET /workspaces/<id>
#############################################################


async def test_get_workspace_being_workspace_member(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == status.HTTP_200_OK, response.text


async def test_get_workspace_being_no_workspace_member(client):
    workspace = await f.create_workspace()

    user2 = await f.create_user()
    client.login(user2)
    response = client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_get_workspace_being_anonymous(client):
    workspace = await f.create_workspace()

    response = client.get(f"/workspaces/{workspace.b64id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_get_workspace_not_found_error(client):
    user = await f.create_user()
    non_existent_id = "xxxxxxxxxxxxxxxxxxxxxx"

    client.login(user)
    response = client.get(f"/workspaces/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


##########################################################
# PATCH /workspaces/<id>/
##########################################################


async def test_update_workspace_200_ok(client):
    workspace = await f.create_workspace()
    data = {"name": "New name"}

    client.login(workspace.created_by)
    response = client.patch(f"/workspaces/{workspace.b64id}", json=data)
    assert response.status_code == status.HTTP_200_OK, response.text
    updated_workspace = response.json()
    assert updated_workspace["name"] == "New name"


async def test_update_workspace_403_forbidden_no_admin(client):
    other_user = await f.create_user()
    workspace = await f.create_workspace()

    data = {"name": "new name"}
    client.login(other_user)
    response = client.patch(f"/workspaces/{workspace.b64id}", json=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_update_workspace_404_not_found_workspace_b64id(client):
    user = await f.create_user()
    data = {"name": "new name"}

    client.login(user)
    response = client.patch(f"/workspaces/{NOT_EXISTING_B64ID}", json=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_update_workspace_422_unprocessable_workspace_b64id(client):
    user = await f.create_user()
    data = {"name": "new name"}

    client.login(user)
    response = client.patch(f"/workspaces/{INVALID_B64ID}", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


#############################################################
#  DELETE /workspaces/<id>
#############################################################


async def test_delete_workspace_being_ws_member(client):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = client.delete(f"/workspaces/{workspace.b64id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.text


async def test_delete_workspace_not_being_ws_member(client):
    user = await f.create_user()
    workspace = await f.create_workspace()

    client.login(user)
    response = client.delete(f"/workspaces/{workspace.b64id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_delete_workspace_not_found(client):
    user = await f.create_user()
    non_existent_id = "xxxxxxxxxxxxxxxxxxxxxx"

    client.login(user)
    response = client.delete(f"/workspaces/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text

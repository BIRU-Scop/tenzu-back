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

pytestmark = pytest.mark.django_db


##########################################################
# LIST /workspaces/<id>/memberships
##########################################################


async def test_list_workspace_memberships(client):
    workspace = await f.create_workspace()
    ws_member = await f.create_user()
    await f.create_workspace_membership(user=ws_member, workspace=workspace)

    client.login(ws_member)
    response = client.get(f"/workspaces/{workspace.b64id}/memberships")
    assert len(response.json()) == 2
    assert response.status_code == status.HTTP_200_OK, response.text


async def test_list_workspace_memberships_wrong_id(client):
    workspace = await f.create_workspace()
    non_existent_id = "xxxxxxxxxxxxxxxxxxxxxx"

    client.login(workspace.created_by)

    response = client.get(f"/workspaces/{non_existent_id}/memberships")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_list_workspace_memberships_not_a_member(client):
    workspace = await f.create_workspace()
    not_a_member = await f.create_user()

    client.login(not_a_member)

    response = client.get(f"/workspaces/{workspace.b64id}/memberships")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


##########################################################
# LIST /workspaces/<id>/guests
##########################################################


async def test_list_workspace_guests(client):
    user = await f.create_user()
    member = await f.create_user()
    workspace = await f.create_workspace(created_by=user)
    project = await f.create_project(created_by=user, workspace=workspace)
    general_role = await f.create_project_role(project=project, is_admin=False)
    await f.create_project_membership(user=member, project=project, role=general_role)

    client.login(user)
    response = client.get(f"/workspaces/{workspace.b64id}/guests")
    assert response.status_code == status.HTTP_200_OK, response.text


async def test_list_workspace_guests_with_pagination(client):
    user = await f.create_user()
    member1 = await f.create_user()
    member2 = await f.create_user()
    workspace = await f.create_workspace(created_by=user)
    project = await f.create_project(created_by=user, workspace=workspace)
    general_role = await f.create_project_role(project=project, is_admin=False)
    await f.create_project_membership(user=member1, project=project, role=general_role)
    await f.create_project_membership(user=member2, project=project, role=general_role)
    offset = 0
    limit = 1

    client.login(user)
    response = client.get(
        f"/workspaces/{workspace.b64id}/guests?offset={offset}&limit={limit}"
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    assert len(response.json()) == 1
    assert response.headers["Pagination-Offset"] == "0"
    assert response.headers["Pagination-Limit"] == "1"


async def test_list_workspace_guests_wrong_id(client):
    workspace = await f.create_workspace()
    non_existent_id = "xxxxxxxxxxxxxxxxxxxxxx"

    client.login(workspace.created_by)

    response = client.get(f"/workspaces/{non_existent_id}/guests")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_list_workspace_guests_not_a_member(client):
    workspace = await f.create_workspace()
    not_a_member = await f.create_user()

    client.login(not_a_member)

    response = client.get(f"/workspaces/{workspace.b64id}/guests")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


##########################################################
# DELETE /workspaces/<id>/memberships/<username>
##########################################################


async def test_delete_workspace_membership(client):
    user = await f.create_user()
    member = await f.create_user()
    workspace = await f.create_workspace(created_by=user)
    await f.create_workspace_membership(workspace=workspace, user=member)

    client.login(user)
    response = client.delete(
        f"/workspaces/{workspace.b64id}/memberships/{member.username}"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.text


async def test_delete_workspace_membership_no_permission(client):
    user = await f.create_user()
    member = await f.create_user()
    workspace = await f.create_workspace(created_by=user)

    client.login(member)
    response = client.delete(
        f"/workspaces/{workspace.b64id}/memberships/{user.username}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_delete_workspace_membership_latest_membership(client):
    user = await f.create_user()
    workspace = await f.create_workspace(created_by=user)

    client.login(user)
    response = client.delete(
        f"/workspaces/{workspace.b64id}/memberships/{user.username}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text

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

from permissions import choices
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# LIST /projects/<id>/memberships
##########################################################


async def test_get_project_memberships(client):
    project = await f.create_project()

    general_member_role = await f.create_project_role(
        project=project,
        permissions=choices.ProjectPermissions.values,
        is_admin=False,
    )

    pj_member = await f.create_user()
    pj_member2 = await f.create_user()
    await f.create_project_membership(
        user=pj_member, project=project, role=general_member_role
    )
    await f.create_project_membership(
        user=pj_member2, project=project, role=general_member_role
    )

    client.login(pj_member)

    response = client.get(f"/projects/{project.b64id}/memberships")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert len(response.json()) == 3


async def test_list_project_memberships_wrong_id(client):
    project = await f.create_project()
    non_existent_id = "xxxxxxxxxxxxxxxxxxxxxx"

    client.login(project.created_by)
    response = client.get(f"/projects/{non_existent_id}/memberships")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_list_project_memberships_not_a_member(client):
    project = await f.create_project()
    not_a_member = await f.create_user()

    client.login(not_a_member)
    response = client.get(f"/projects/{project.b64id}/memberships")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


##########################################################
# PATCH /projects/<id>/memberships/<username>
##########################################################


async def test_update_project_membership_role_membership_not_exist(client):
    project = await f.create_project()

    client.login(project.created_by)
    username = "not_exist"
    data = {"role_slug": "general"}
    response = client.patch(
        f"projects/{project.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_update_project_membership_role_user_without_permission(client):
    project = await f.create_project()
    user = await f.create_user()
    general_member_role = await f.create_project_role(
        project=project,
        permissions=choices.ProjectPermissions.values,
        is_admin=False,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(user)
    username = project.created_by.username
    data = {"role_slug": "general"}
    response = client.patch(
        f"/projects/{project.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_update_project_membership_role_ok(client):
    project = await f.create_project()
    user = await f.create_user()
    general_member_role = await f.create_project_role(
        project=project,
        permissions=choices.ProjectPermissions.values,
        is_admin=False,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(project.created_by)
    username = user.username
    data = {"role_slug": "admin"}
    response = client.patch(
        f"projects/{project.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_200_OK, response.text


##########################################################
# DELETE /projects/<id>/memberships/<username>
##########################################################


async def test_delete_project_membership_not_exist(client):
    project = await f.create_project()
    username = "not_exist"

    client.login(project.created_by)
    response = client.delete(f"/projects/{project.b64id}/memberships/{username}")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_delete_project_membership_without_permissions(client):
    project = await f.create_project()
    member = await f.create_user()
    general_member_role = await f.create_project_role(
        project=project,
        permissions=choices.ProjectPermissions.values,
        is_admin=False,
    )
    await f.create_project_membership(
        user=member, project=project, role=general_member_role
    )

    client.login(member)
    response = client.delete(
        f"/projects/{project.b64id}/memberships/{project.created_by.username}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_delete_project_membership_project_admin(client):
    project = await f.create_project()
    member = await f.create_user()
    general_member_role = await f.create_project_role(
        project=project,
        permissions=choices.ProjectPermissions.values,
        is_admin=False,
    )
    await f.create_project_membership(
        user=member, project=project, role=general_member_role
    )

    client.login(project.created_by)
    response = client.delete(f"/projects/{project.b64id}/memberships/{member.username}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.text


async def test_delete_project_membership_self_request(client):
    project = await f.create_project()
    member = await f.create_user()
    general_member_role = await f.create_project_role(
        project=project,
        permissions=choices.ProjectPermissions.values,
        is_admin=False,
    )
    await f.create_project_membership(
        user=member, project=project, role=general_member_role
    )

    client.login(member)
    response = client.delete(f"/projects/{project.b64id}/memberships/{member.username}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.text

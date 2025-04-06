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

pytestmark = pytest.mark.django_db


##########################################################
# LIST /projects/<id>/memberships
##########################################################


async def test_list_project_memberships(client, project_template):
    project = await f.create_project(project_template)

    general_member_role = await f.create_project_role(
        project=project,
        permissions=[],
        is_owner=False,
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

    response = await client.get(f"/projects/{project.b64id}/memberships")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert len(response.json()) == 3  # 2 explicitly created + owner membership


async def test_list_project_memberships_wrong_id(client, project_template):
    project = await f.create_project(project_template)
    non_existent_id = "xxxxxxxxxxxxxxxxxxxxxx"

    client.login(project.created_by)
    response = await client.get(f"/projects/{non_existent_id}/memberships")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_list_project_memberships_not_a_member(client, project_template):
    project = await f.create_project(project_template)
    not_a_member = await f.create_user()

    client.login(not_a_member)
    response = await client.get(f"/projects/{project.b64id}/memberships")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text

    # even invitee can't see members
    general_admin_role = await f.create_project_role(
        project=project,
        permissions=choices.ProjectPermissions.values,
        is_owner=False,
    )
    await f.create_project_invitation(
        email=not_a_member.email,
        user=not_a_member,
        project=project,
        role=general_admin_role,
        status=InvitationStatus.PENDING,
    )
    response = await client.get(f"/projects/{project.b64id}/memberships")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


##########################################################
# PATCH /projects/<id>/memberships/<username>
##########################################################


async def test_update_project_membership_role_membership_not_exist(
    client, project_template
):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    username = "not_exist"
    data = {"role_slug": "member"}
    response = await client.patch(
        f"projects/{project.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_update_project_membership_role_user_without_permission(
    client, project_template
):
    project = await f.create_project(project_template)
    user1 = await f.create_user()
    user2 = await f.create_user()
    general_member_role = await f.create_project_role(
        project=project,
        permissions=[],
        is_owner=False,
    )
    await f.create_project_membership(
        user=user1, project=project, role=general_member_role
    )
    await f.create_project_membership(
        user=user2, project=project, role=general_member_role
    )

    client.login(user1)
    username = user2.username
    data = {"role_slug": "member"}
    response = await client.patch(
        f"/projects/{project.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_update_project_membership_role_ok(client, project_template):
    project = await f.create_project(project_template)
    user1 = await f.create_user()
    user2 = await f.create_user()
    general_admin_role = await f.create_project_role(
        project=project,
        permissions=[choices.ProjectPermissions.CREATE_MODIFY_MEMBER.value],
        is_owner=False,
    )
    await f.create_project_membership(
        user=user1, project=project, role=general_admin_role
    )
    await f.create_project_membership(
        user=user2, project=project, role=general_admin_role
    )

    client.login(user1)
    username = user2.username
    data = {"role_slug": "member"}
    response = await client.patch(
        f"projects/{project.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_200_OK, response.text


async def test_update_project_membership_role_owner_and_not_owner(
    client, project_template
):
    project = await f.create_project(project_template)
    user1 = await f.create_user()
    user2 = await f.create_user()
    general_admin_role = await f.create_project_role(
        project=project,
        permissions=[choices.ProjectPermissions.CREATE_MODIFY_MEMBER.value],
        is_owner=False,
    )
    await f.create_project_membership(
        user=user1, project=project, role=general_admin_role
    )
    await f.create_project_membership(
        user=user2, project=project, role=general_admin_role
    )

    client.login(user1)
    # change role to owner
    username = user2.username
    data = {"role_slug": "owner"}
    response = await client.patch(
        f"/projects/{project.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
    # change role of owner
    username = project.created_by.username
    data = {"role_slug": "member"}
    response = await client.patch(
        f"/projects/{project.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_update_project_membership_role_owner_and_owner(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    general_member_role = await f.create_project_role(
        project=project,
        permissions=[],
        is_owner=False,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_member_role
    )

    client.login(project.created_by)
    # change role to owner
    username = user.username
    data = {"role_slug": "owner"}
    response = await client.patch(
        f"/projects/{project.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    # change role of owner
    data = {"role_slug": "member"}
    response = await client.patch(
        f"/projects/{project.b64id}/memberships/{username}", json=data
    )
    assert response.status_code == status.HTTP_200_OK, response.text


##########################################################
# DELETE /projects/<id>/memberships/<username>
##########################################################


async def test_delete_project_membership_not_exist(client, project_template):
    project = await f.create_project(project_template)
    username = "not_exist"

    client.login(project.created_by)
    response = await client.delete(f"/projects/{project.b64id}/memberships/{username}")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_delete_project_membership_without_permissions(client, project_template):
    project = await f.create_project(project_template)
    user1 = await f.create_user()
    user2 = await f.create_user()
    general_member_role = await f.create_project_role(
        project=project,
        permissions=[],
        is_owner=False,
    )
    await f.create_project_membership(
        user=user1, project=project, role=general_member_role
    )
    await f.create_project_membership(
        user=user2, project=project, role=general_member_role
    )

    client.login(user1)
    response = await client.delete(
        f"/projects/{project.b64id}/memberships/{user2.username}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_delete_project_membership_role_ok(client, project_template):
    project = await f.create_project(project_template)
    user1 = await f.create_user()
    user2 = await f.create_user()
    general_admin_role = await f.create_project_role(
        project=project,
        permissions=[choices.ProjectPermissions.DELETE_MEMBER.value],
        is_owner=False,
    )
    await f.create_project_membership(
        user=user1, project=project, role=general_admin_role
    )
    await f.create_project_membership(
        user=user2, project=project, role=general_admin_role
    )

    client.login(user1)
    response = await client.delete(
        f"/projects/{project.b64id}/memberships/{user2.username}"
    )
    assert response.status_code == status.HTTP_200_OK, response.text


async def test_delete_project_membership_only_owner(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/memberships/{project.created_by.username}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text


async def test_delete_project_membership_role_owner_and_not_owner(
    client, project_template
):
    project = await f.create_project(project_template)
    user = await f.create_user()
    general_admin_role = await f.create_project_role(
        project=project,
        permissions=[choices.ProjectPermissions.DELETE_MEMBER.value],
        is_owner=False,
    )
    await f.create_project_membership(
        user=user, project=project, role=general_admin_role
    )

    client.login(user)
    response = await client.delete(
        f"/projects/{project.b64id}/memberships/{project.created_by.username}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_delete_project_membership_role_owner_and_owner(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    owner_role = await project.roles.aget(is_owner=True)
    await f.create_project_membership(user=user, project=project, role=owner_role)

    client.login(project.created_by)
    response = await client.delete(
        f"/projects/{project.b64id}/memberships/{user.username}"
    )
    assert response.status_code == status.HTTP_200_OK, response.text


async def test_delete_project_membership_self_request(client, project_template):
    project = await f.create_project(project_template)
    member = await f.create_user()
    general_member_role = await f.create_project_role(
        project=project,
        permissions=[],
        is_owner=False,
    )
    await f.create_project_membership(
        user=member, project=project, role=general_member_role
    )

    client.login(member)
    response = await client.delete(
        f"/projects/{project.b64id}/memberships/{member.username}"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.text


##########################################################
# LIST /projects/<id>/roles
##########################################################


async def test_list_project_roles(client, project_template):
    project = await f.create_project(project_template)

    general_member_role = await f.create_project_role(
        project=project,
        permissions=[],
        is_owner=False,
    )

    pj_member = await f.create_user()
    await f.create_project_membership(
        user=pj_member, project=project, role=general_member_role
    )

    client.login(pj_member)

    response = await client.get(f"/projects/{project.b64id}/roles")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert len(response.json()) == 5  # 4 default + newly created


async def test_list_project_roles_wrong_id(client, project_template):
    project = await f.create_project(project_template)
    non_existent_id = "xxxxxxxxxxxxxxxxxxxxxx"

    client.login(project.created_by)
    response = await client.get(f"/projects/{non_existent_id}/roles")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_list_project_roles_not_a_member(client, project_template):
    project = await f.create_project(project_template)
    not_a_member = await f.create_user()

    client.login(not_a_member)
    response = await client.get(f"/projects/{project.b64id}/roles")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text

    # even invitee can't see members
    general_admin_role = await f.create_project_role(
        project=project,
        permissions=choices.ProjectPermissions.values,
        is_owner=False,
    )
    await f.create_project_invitation(
        email=not_a_member.email,
        user=not_a_member,
        project=project,
        role=general_admin_role,
        status=InvitationStatus.PENDING,
    )
    response = await client.get(f"/projects/{project.b64id}/roles")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


#########################################################################
# PUT /projects/<project_id>/roles/<role_slug>
#########################################################################


async def test_update_project_role_permissions_anonymous_user(client, project_template):
    project = await f.create_project(project_template)
    role_slug = "member"
    data = {"permissions": [choices.ProjectPermissions.VIEW_STORY.value]}

    response = await client.put(
        f"/projects/{project.b64id}/roles/{role_slug}", json=data
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


async def test_update_project_role_permissions_project_not_found(client):
    user = await f.create_user()
    data = {"permissions": [choices.ProjectPermissions.VIEW_STORY.value]}
    non_existent_id = "xxxxxxxxxxxxxxxxxxxxxx"

    client.login(user)
    response = await client.put(
        f"/projects/{non_existent_id}/roles/role-slug", json=data
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_update_project_role_permissions_role_not_found(client, project_template):
    project = await f.create_project(project_template)
    non_existent_role_slug = "role-slug"
    data = {"permissions": [choices.ProjectPermissions.VIEW_STORY.value]}

    client.login(project.created_by)
    response = await client.put(
        f"/projects/{project.b64id}/roles/{non_existent_role_slug}", json=data
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


async def test_update_project_role_permissions_user_without_permission(
    client, project_template
):
    user = await f.create_user()
    project = await f.create_project(project_template)
    role_slug = "member"
    data = {"permissions": [choices.ProjectPermissions.VIEW_STORY.value]}

    client.login(user)
    response = await client.put(
        f"/projects/{project.b64id}/roles/{role_slug}", json=data
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_update_project_role_permissions_role_non_editable(
    client, project_template
):
    project = await f.create_project(project_template)
    role_slug = "admin"
    data = {"permissions": [choices.ProjectPermissions.VIEW_STORY.value]}

    client.login(project.created_by)
    response = await client.put(
        f"/projects/{project.b64id}/roles/{role_slug}", json=data
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_update_project_role_permissions_incompatible_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    role_slug = "member"
    data = {"permissions": [choices.ProjectPermissions.MODIFY_STORY.value]}

    client.login(project.created_by)
    response = await client.put(
        f"/projects/{project.b64id}/roles/{role_slug}", json=data
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


async def test_update_project_role_permissions_not_valid_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    role_slug = "member"
    data = {"permissions": ["not_valid", "foo"]}

    client.login(project.created_by)
    response = await client.put(
        f"/projects/{project.b64id}/roles/{role_slug}", json=data
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


async def test_update_project_role_permissions_ok(client, project_template):
    project = await f.create_project(project_template)
    pj_member = await f.create_user()
    general_admin_role = await f.create_project_role(
        project=project,
        permissions=[choices.ProjectPermissions.CREATE_MODIFY_DELETE_ROLE.value],
        is_owner=False,
    )
    await f.create_project_membership(
        user=pj_member, project=project, role=general_admin_role
    )
    role_slug = "member"
    data = {"permissions": [choices.ProjectPermissions.VIEW_STORY.value]}

    client.login(pj_member)
    response = await client.put(
        f"/projects/{project.b64id}/roles/{role_slug}", json=data
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert data["permissions"] == response.json()["permissions"]

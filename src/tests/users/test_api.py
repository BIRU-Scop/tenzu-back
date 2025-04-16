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

from datetime import timedelta
from unittest import mock

import pytest

from comments.models import Comment
from projects.invitations.models import ProjectInvitation
from projects.invitations.services import _generate_project_invitation_token
from projects.memberships.models import ProjectMembership
from projects.projects.models import Project
from stories.assignments.models import StoryAssignment
from stories.stories.models import Story
from tests.utils import factories as f
from users.models import User
from users.services import _generate_reset_password_token, _generate_verify_user_token
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.invitations.services import _generate_workspace_invitation_token
from workspaces.memberships.models import WorkspaceMembership
from workspaces.workspaces.models import Workspace

pytestmark = pytest.mark.django_db


##########################################################
# POST /users
##########################################################


async def test_create_user_ok_with_token_project(client):
    data = {
        "email": "test.create@email.com",
        "fullName": "Ada Lovelace",
        "color": 8,
        "password": "correctP4ssword%",
        "acceptTerms": True,
        "projectInvitationToken": "eyJ0eXAiOToken",
        "accept_project_invitation": False,
        "lang": "es-ES",
    }

    response = await client.post("/users", json=data)
    assert response.status_code == 200, response.data


async def test_create_user_ok_with_token_workspace(client):
    data = {
        "email": "test.create@email.com",
        "fullName": "Ada Lovelace",
        "color": 8,
        "password": "correctP4ssword%",
        "acceptTerms": True,
        "workspaceInvitationToken": "eyJ0eXAiOToken",
        "accept_workspace_invitation": False,
        "lang": "es-ES",
    }

    response = await client.post("/users", json=data)
    assert response.status_code == 200, response.data


async def test_create_user_email_already_exists(client):
    user = await f.create_user()
    data = {
        "email": user.email,
        "fullName": "Ada Lovelace",
        "password": "correctP4ssword%",
        "acceptTerms": True,
    }
    response = await client.post("/users", json=data)
    assert response.status_code == 400, response.data


##########################################################
# POST /users/verify
##########################################################


async def test_verify_user_ok(client):
    user = await f.create_user(is_active=False)

    data = {"token": await _generate_verify_user_token(user)}

    response = await client.post("/users/verify", json=data)
    assert response.status_code == 200, response.data
    assert response.json()["projectInvitation"] is None


async def test_verify_user_ok_accepting_pj_invitation(client, project_template):
    user = await f.create_user(is_active=False)
    project = await f.create_project(project_template)
    role = await f.create_project_role(project=project)
    project_invitation = await f.create_project_invitation(
        project=project, role=role, email=user.email
    )

    project_invitation_token = await _generate_project_invitation_token(
        project_invitation
    )
    data = {
        "token": await _generate_verify_user_token(
            user=user, project_invitation_token=project_invitation_token
        )
    }

    response = await client.post("/users/verify", json=data)
    assert response.status_code == 200, response.data
    assert response.json()["projectInvitation"] is not None


async def test_verify_user_ok_accepting_ws_invitation(client):
    user = await f.create_user(is_active=False)
    workspace = await f.create_workspace()
    workspace_invitation = await f.create_workspace_invitation(
        workspace=workspace, email=user.email
    )

    workspace_invitation_token = await _generate_workspace_invitation_token(
        workspace_invitation
    )
    data = {
        "token": await _generate_verify_user_token(
            user=user, workspace_invitation_token=workspace_invitation_token
        )
    }

    response = await client.post("/users/verify", json=data)
    assert response.status_code == 200, response.data
    assert response.json()["workspaceInvitation"] is not None


async def test_verify_user_ok_with_invalid_pj_invitation(client):
    user = await f.create_user(is_active=False)

    project_invitation_token = "invalid-invitation-token"
    data = {"token": await _generate_verify_user_token(user, project_invitation_token)}

    response = await client.post("/users/verify", json=data)
    assert response.status_code == 200, response.data
    assert response.json()["projectInvitation"] is None


async def test_verify_user_ok_with_invalid_ws_invitation(client):
    user = await f.create_user(is_active=False)

    workspace_invitation_token = "invalid-invitation-token"
    data = {
        "token": await _generate_verify_user_token(user, workspace_invitation_token)
    }

    response = await client.post("/users/verify", json=data)
    assert response.status_code == 200, response.data
    assert response.json()["workspaceInvitation"] is None


async def test_verify_user_error_invalid_token(client):
    data = {"token": "invalid token"}

    response = await client.post("/users/verify", json=data)
    assert response.status_code == 400, response.data


async def test_verify_user_error_expired_token(client):
    with mock.patch(
        "users.tokens.VerifyUserToken.lifetime",
        new_callable=mock.PropertyMock(return_value=timedelta(days=-1)),
    ):
        user = await f.create_user(is_active=False)

        data = {"token": await _generate_verify_user_token(user)}

        response = await client.post("/users/verify", json=data)
        assert response.status_code == 400, response.data


async def test_verify_user_error_used_token(client):
    user = await f.create_user(is_active=False)

    data = {"token": await _generate_verify_user_token(user)}

    response = await client.post("/users/verify", json=data)
    assert response.status_code == 200, response.data
    response = await client.post("/users/verify", json=data)
    assert response.status_code == 400, response.data


##########################################################
# GET /my/user
##########################################################


async def test_my_user_error_no_authenticated_user(client):
    response = await client.get("/my/user")

    assert response.status_code == 401


async def test_my_user_success(client):
    user = await f.create_user()

    client.login(user)
    response = await client.get("/my/user")

    assert response.status_code == 200
    assert "email" in response.json().keys()


##########################################################
# PUT /my/user
##########################################################


async def test_update_my_user_error_no_authenticated_user(client):
    data = {
        "fullName": "Ada Lovelace",
        "lang": "es-ES",
    }
    response = await client.put("/my/user", json=data)

    assert response.status_code == 401


async def test_update_my_user_success(client):
    user = await f.create_user()
    data = {
        "fullName": "Ada Lovelace",
        "lang": "es-ES",
    }

    client.login(user)
    response = await client.put("/my/user", json=data)

    assert response.status_code == 200, response.data


#####################################################################
# DELETE /my/user
#####################################################################


async def test_delete_user_204_ok(client):
    user = await f.create_user(username="user", is_active=True)

    client.login(user)
    response = await client.delete("/my/user")
    assert response.status_code == 204, response.data
    assert not await User.objects.aexists()


async def test_delete_user_204_complex_data(client, project_template):
    user = await f.create_user(username="user", is_active=True)
    other_user = await f.create_user(username="other_user", is_active=True)
    # user only ws and pj member
    ws1 = await f.create_workspace(created_by=user)
    pj1_ws1 = await f.create_project(project_template, created_by=user, workspace=ws1)
    pj1_ws1_story1 = await f.create_story(project=pj1_ws1, created_by=user)
    await f.create_story_assignment(story=pj1_ws1_story1, user=user)
    await f.create_comment(content_object=pj1_ws1_story1)

    # user not only ws owner
    ws2 = await f.create_workspace(created_by=user)
    owner_role = await ws2.roles.aget(is_owner=True)
    await f.create_workspace_membership(user=other_user, workspace=ws2, role=owner_role)
    # user not only pj owner
    pj1_ws2 = await f.create_project(project_template, created_by=user, workspace=ws2)
    owner_role = await pj1_ws2.roles.aget(is_owner=True)
    await f.create_project_membership(user=other_user, project=pj1_ws2, role=owner_role)
    pj1_ws2_story1 = await f.create_story(project=pj1_ws2, created_by=user)
    await f.create_story_assignment(story=pj1_ws2_story1, user=user)
    await f.create_comment(content_object=pj1_ws2_story1)
    await f.create_comment(content_object=pj1_ws2_story1, created_by=other_user)
    pj1_ws2_story2 = await f.create_story(project=pj1_ws2, created_by=other_user)
    await f.create_story_assignment(story=pj1_ws2_story2, user=user)
    await f.create_comment(content_object=pj1_ws2_story2)

    # user not member
    ws3 = await f.create_workspace(created_by=other_user)
    await f.create_project(project_template, created_by=other_user, workspace=ws3)

    # user ws member but not ws owner
    ws4 = await f.create_workspace(created_by=other_user)
    await f.create_workspace_membership(user=user, workspace=ws4)
    # user pj member but not pj owner
    pj1_ws4 = await f.create_project(
        project_template, created_by=other_user, workspace=ws4
    )
    await f.create_project_membership(user=user, project=pj1_ws4)
    pj1_ws4_story1 = await f.create_story(project=pj1_ws4, created_by=other_user)
    await f.create_story_assignment(story=pj1_ws4_story1, user=other_user)
    await f.create_story(project=pj1_ws4, created_by=user)
    # user only pj member
    await f.create_project(project_template, created_by=user, workspace=ws4)

    # user only ws member, without project
    ws5 = await f.create_workspace(created_by=user)

    # ws invitations
    ws6 = await f.create_workspace(created_by=other_user)
    await f.create_workspace_invitation(user=user, workspace=ws6)
    # pj invitations
    ws7 = await f.create_workspace(created_by=other_user)
    pj1_ws7 = await f.create_project(
        project_template, created_by=other_user, workspace=ws7
    )
    await f.create_project_invitation(user=user, project=pj1_ws7)

    client.login(user)
    response = await client.delete("/my/user")
    assert response.status_code == 204, response.data

    with pytest.raises(User.DoesNotExist):
        await user.arefresh_from_db()

    assert await Workspace.objects.acount() == 5
    assert await Project.objects.acount() == 4
    assert await WorkspaceMembership.objects.acount() == 5
    assert await ProjectMembership.objects.acount() == 4
    assert not await WorkspaceInvitation.objects.aexists()
    assert not await ProjectInvitation.objects.aexists()

    assert await Story.objects.acount() == 4
    assert await Story.objects.filter(created_by__isnull=True).acount() == 2
    assert await StoryAssignment.objects.acount() == 1
    assert await Comment.objects.acount() == 3
    assert await Comment.objects.filter(created_by__isnull=True).acount() == 1


async def test_delete_user_400_only_owner(client, project_template):
    user = await f.create_user(username="user", is_active=True)
    # only ws owner
    ws1 = await f.create_workspace(created_by=user)
    await f.create_workspace_membership(workspace=ws1)

    client.login(user)
    response = await client.delete("/my/user")
    assert response.status_code == 400, response.data

    # not only ws owner but only pj owner
    owner_role = await ws1.roles.aget(is_owner=True)
    await f.create_workspace_membership(workspace=ws1, role=owner_role)
    pj1_ws1 = await f.create_project(project_template, created_by=user, workspace=ws1)
    await f.create_project_membership(project=pj1_ws1)
    response = await client.delete("/my/user")
    assert response.status_code == 400, response.data


async def test_delete_user_401_unauthorized_user(client):
    response = await client.get("/my/user")

    assert response.status_code == 401


#####################################################################
# GET /my/user/delete-info
#####################################################################


async def test_get_user_delete_info_no_authenticated_user(client):
    response = await client.get("/my/user/delete-info")

    assert response.status_code == 401


async def test_get_user_delete_info_success(client, project_template):
    user = await f.create_user(username="user", is_active=True)
    other_user = await f.create_user(username="other_user", is_active=True)
    # user only ws and pj member
    ws1 = await f.create_workspace(name="ws1", created_by=user)
    pj1_ws1 = await f.create_project(
        project_template, name="pj1_ws1", created_by=user, workspace=ws1
    )

    # user not only ws owner
    ws2 = await f.create_workspace(name="ws2", created_by=user)
    owner_role = await ws2.roles.aget(is_owner=True)
    await f.create_workspace_membership(user=other_user, workspace=ws2, role=owner_role)
    # user not only pj owner
    pj1_ws2 = await f.create_project(
        project_template, name="pj1_ws2", created_by=user, workspace=ws2
    )
    owner_role = await pj1_ws2.roles.aget(is_owner=True)
    await f.create_project_membership(user=other_user, project=pj1_ws2, role=owner_role)

    # user not member
    ws3 = await f.create_workspace(name="ws3", created_by=other_user)
    await f.create_project(
        project_template, name="pj1_ws3", created_by=other_user, workspace=ws3
    )

    # user ws member but not ws owner
    ws4 = await f.create_workspace(name="ws4", created_by=other_user)
    await f.create_workspace_membership(user=user, workspace=ws4)
    # user pj member but not pj owner
    pj1_ws4 = await f.create_project(
        project_template, name="pj1_ws4", created_by=other_user, workspace=ws4
    )
    await f.create_project_membership(user=user, project=pj1_ws4)
    # user only pj member
    pj2_ws4 = await f.create_project(
        project_template, name="pj2_ws4", created_by=user, workspace=ws4
    )

    # user only ws member, without project
    ws5 = await f.create_workspace(name="ws5", created_by=user)

    # only ws owner without project
    ws6 = await f.create_workspace(name="ws6", created_by=user)
    await f.create_workspace_membership(workspace=ws6, user=other_user)

    # only ws owner with projects
    ws7 = await f.create_workspace(name="ws7", created_by=user)
    await f.create_workspace_membership(workspace=ws7, user=other_user)
    # only pj owner
    pj1_ws7 = await f.create_project(
        project_template, name="pj1_ws7", created_by=user, workspace=ws7
    )
    await f.create_project_membership(project=pj1_ws7, user=other_user)
    # not only pj owner
    pj2_ws7 = await f.create_project(
        project_template, name="pj2_ws7", created_by=user, workspace=ws7
    )
    owner_role = await pj2_ws7.roles.aget(is_owner=True)
    await f.create_project_membership(project=pj2_ws7, user=other_user, role=owner_role)
    # not member
    await f.create_project(project_template, created_by=other_user, workspace=ws7)

    # not only ws owner but only pj owner
    ws8 = await f.create_workspace(name="ws8", created_by=user)
    owner_role = await ws8.roles.aget(is_owner=True)
    await f.create_workspace_membership(workspace=ws8, role=owner_role, user=other_user)
    pj1_ws8 = await f.create_project(
        project_template, name="pj1_ws8", created_by=user, workspace=ws8
    )
    await f.create_project_membership(project=pj1_ws8, user=other_user)

    client.login(user)
    response = await client.get("/my/user/delete-info")
    assert response.status_code == 200, response.data
    res = response.json()
    assert len(res) == 4
    assert res.keys() == {
        "onlyOwnerCollectiveWorkspaces",
        "onlyOwnerCollectiveProjects",
        "onlyMemberWorkspaces",
        "onlyMemberProjects",
    }

    assert [ws["name"] for ws in res["onlyOwnerCollectiveWorkspaces"]] == [
        ws6.name,
        ws7.name,
    ]
    assert [ws["name"] for ws in res["onlyOwnerCollectiveProjects"]] == [
        pj1_ws7.name,
        pj1_ws8.name,
    ]
    assert [ws["name"] for ws in res["onlyMemberWorkspaces"]] == [ws1.name, ws5.name]
    assert [pj["name"] for pj in res["onlyMemberWorkspaces"][0]["projects"]] == [
        pj1_ws1.name
    ]
    assert [ws["name"] for ws in res["onlyMemberProjects"]] == [pj2_ws4.name]


##########################################################
# POST /users/reset-password
##########################################################


async def test_request_reset_password_ok(client):
    user = await f.create_user(is_active=False)

    data = {"email": user.email}

    response = await client.post("/users/reset-password", json=data)
    assert response.status_code == 200, response.data


async def test_request_reset_password_ok_with_no_registered_email(client):
    data = {"email": "unregistered@email.com"}

    response = await client.post("/users/reset-password", json=data)
    assert response.status_code == 200, response.data


async def test_request_reset_password_ok_with_invalid_email(client):
    data = {"email": "invalid@email"}

    response = await client.post("/users/reset-password", json=data)
    assert response.status_code == 422, response.data
    assert response.json()["detail"][0]["type"] == "value_error"


async def test_request_reset_password_error_with_no_email(client):
    data = {}

    response = await client.post("/users/reset-password", json=data)
    assert response.status_code == 422, response.data
    assert response.json()["detail"][0]["type"] == "missing"


##########################################################
# GET /users/reset-password/{token}/verify
##########################################################


async def test_verify_reset_password_token(client):
    user = await f.create_user()
    token = await _generate_reset_password_token(user)

    response = await client.get(f"/users/reset-password/{token}/verify")
    assert response.status_code == 200, response.data
    assert response.json() is True


async def test_verify_reset_password_error_inactive_user(client):
    user = await f.create_user(is_active=False)
    token = await _generate_reset_password_token(user)

    response = await client.get(f"/users/reset-password/{token}/verify")
    assert response.status_code == 400, response.data


async def test_verify_reset_password_error_invalid_token(client):
    token = "invalid_token"

    response = await client.get(f"/users/reset-password/{token}/verify")
    assert response.status_code == 400, response.data


async def test_verify_reset_password_error_used_token(client):
    user = await f.create_user()
    token = await _generate_reset_password_token(user)
    data = {"password": "123123.a"}

    response = await client.post(f"/users/reset-password/{token}", json=data)
    assert response.status_code == 200, response.data
    response = await client.get(f"/users/reset-password/{token}/verify")
    assert response.status_code == 400, response.data


async def test_verify_reset_password_error_expired_token(client):
    with mock.patch(
        "users.tokens.ResetPasswordToken.lifetime",
        new_callable=mock.PropertyMock(return_value=timedelta(days=-1)),
    ):
        user = await f.create_user()
        token = await _generate_reset_password_token(user)

        response = await client.get(f"/users/reset-password/{token}/verify")
        assert response.status_code == 400, response.data


##########################################################
# POST /users/reset-password/{token}
##########################################################


async def test_reset_password_ok(client):
    user = await f.create_user()
    token = await _generate_reset_password_token(user)
    data = {"password": "123123.a"}

    response = await client.post(f"/users/reset-password/{token}", json=data)
    assert response.status_code == 200, response.data
    assert "access" in response.json()
    assert "refresh" in response.json()


async def test_reset_password_error_with_no_password(client):
    user = await f.create_user()
    token = await _generate_reset_password_token(user)
    data = {}

    response = await client.post(f"/users/reset-password/{token}", json=data)
    assert response.status_code == 422, response.data
    assert response.json()["detail"][0]["type"] == "missing"


async def test_reset_password_error_with_invalid_password(client):
    user = await f.create_user()
    token = await _generate_reset_password_token(user)
    data = {"password": "123123"}

    response = await client.post(f"/users/reset-password/{token}", json=data)
    assert response.status_code == 422, response.data
    assert response.json()["detail"][0]["type"] == "string_too_short"


async def test_reset_password_error_inactive_user(client):
    user = await f.create_user(is_active=False)
    token = await _generate_reset_password_token(user)
    data = {"password": "123123.a"}

    response = await client.post(f"/users/reset-password/{token}", json=data)
    assert response.status_code == 400, response.data


async def test_reset_password_error_invalid_token(client):
    token = "invalid_token"
    data = {"password": "123123.a"}

    response = await client.post(f"/users/reset-password/{token}", json=data)
    assert response.status_code == 400, response.data


async def test_reset_password_error_used_token(client):
    user = await f.create_user()
    token = await _generate_reset_password_token(user)
    data = {"password": "123123.a"}

    response = await client.post(f"/users/reset-password/{token}", json=data)
    assert response.status_code == 200, response.data
    response = await client.post(f"/users/reset-password/{token}", json=data)
    assert response.status_code == 400, response.data


async def test_reset_password_error_expired_token(client):
    with mock.patch(
        "users.tokens.ResetPasswordToken.lifetime",
        new_callable=mock.PropertyMock(return_value=timedelta(days=-1)),
    ):
        user = await f.create_user()
        token = await _generate_reset_password_token(user)
        data = {"password": "123123.a"}

        response = await client.post(f"/users/reset-password/{token}", json=data)
        assert response.status_code == 400, response.data

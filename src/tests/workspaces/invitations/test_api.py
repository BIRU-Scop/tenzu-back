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

from memberships.choices import InvitationStatus
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID, NOT_EXISTING_SLUG
from workspaces.invitations.tokens import WorkspaceInvitationToken

pytestmark = pytest.mark.django_db


##########################################################
# POST /workspaces/<id>/invitations
##########################################################


async def test_create_workspace_invitations_200_ok(client):
    invitee1 = await f.create_user(email="invitee1@tenzu.demo", username="invitee1")
    await f.create_user(email="invitee2@tenzu.demo", username="invitee2")
    workspace = await f.create_workspace()
    data = {
        "invitations": [
            {"email": "invitee2@tenzu.demo", "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "member"},
            {"username": invitee1.username, "role_slug": "member"},
        ]
    }
    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 200, response.data


async def test_create_workspace_invitations_400_bad_request_not_existing_username(
    client,
):
    workspace = await f.create_workspace()
    data = {"invitations": [{"username": "not-a-username", "role_slug": "owner"}]}
    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 400, response.data


async def test_create_workspace_invitations_non_existing_role(client):
    workspace = await f.create_workspace()
    data = {
        "invitations": [
            {"email": "test@email.com", "role_slug": NOT_EXISTING_SLUG},
        ]
    }
    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 400, response.data


async def test_create_workspace_invitations_401_not_authorised_anonymous_user(client):
    workspace = await f.create_workspace()
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "owner"},
        ]
    }
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 401, response.text


async def test_create_workspace_invitations_403_forbidden_user_without_permission(
    client,
):
    workspace = await f.create_workspace()
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "owner"},
        ]
    }
    user = await f.create_user()
    client.login(user)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 403, response.text


async def test_create_workspace_invitations_404_not_found_workspace_b64id(client):
    user = await f.create_user()
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "owner"},
        ]
    }
    client.login(user)
    response = await client.post(
        f"/workspaces/{NOT_EXISTING_B64ID}/invitations", json=data
    )
    assert response.status_code == 404, response.text


async def test_create_workspace_invitations_422_unprocessable_workspace_b64id(client):
    user = await f.create_user()
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "owner"},
        ]
    }
    client.login(user)
    response = await client.post(f"/workspaces/{INVALID_B64ID}/invitations", json=data)
    assert response.status_code == 422, response.text


##########################################################
# LIST /workspaces/<id>/invitations
##########################################################


async def test_list_workspaces_invitations_200_ok(client):
    workspace = await f.create_workspace()

    user1 = await f.create_user(full_name="AAA")
    await f.create_workspace_invitation(
        email=user1.email,
        user=user1,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )
    user2 = await f.create_user(full_name="BBB")
    await f.create_workspace_invitation(
        email=user2.email,
        user=user2,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )
    await f.create_workspace_invitation(
        email="non-existing@email.com",
        user=None,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )
    user3 = await f.create_user()
    await f.create_workspace_invitation(
        email=user3.email,
        user=user3,
        workspace=workspace,
        status=InvitationStatus.ACCEPTED,
    )

    client.login(workspace.created_by)

    response = await client.get(f"/workspaces/{workspace.b64id}/invitations")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 3


async def test_list_workspaces_invitations_403_forbidden_no_permissions(client):
    workspace = await f.create_workspace()
    user1 = await f.create_user(full_name="AAA")
    client.login(user1)
    response = await client.get(f"/workspaces/{workspace.b64id}/invitations")
    assert response.status_code == 403, response.text


async def test_list_workspaces_404_not_found_workspace_b64id(client):
    workspace = await f.create_workspace()
    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{NOT_EXISTING_B64ID}/invitations")
    assert response.status_code == 404, response.text


async def test_list_workspaces_422_unprocessable_workspace_b64id(client):
    workspace = await f.create_workspace()
    client.login(workspace.created_by)
    offset = 0
    limit = 1
    response = await client.get(
        f"/workspaces/{INVALID_B64ID}/invitations?offset={offset}&limit={limit}"
    )
    assert response.status_code == 422, response.text


#########################################################################
# GET /workspaces/invitations/<token>
#########################################################################


async def test_get_workspace_invitation_200_ok(client):
    invitation = await f.create_workspace_invitation()
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    response = await client.get(f"/workspaces/invitations/{str(token)}")
    assert response.status_code == 200, response.text


async def test_get_workspace_invitation_400_bad_request_invalid_token(client):
    response = await client.get("/workspaces/invitations/invalid-token")
    assert response.status_code == 400, response.text


async def test_get_workspace_invitation_404_not_found_token(client):
    invitation = f.build_workspace_invitation(id=111)
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    response = await client.get(f"/workspaces/invitations/{str(token)}")
    assert response.status_code == 404, response.text


#########################################################################
# POST /workspaces/invitations/<token>/accept
#########################################################################


async def test_accept_workspace_invitation_200_ok(client):
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(email=user.email)
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    client.login(user)
    response = await client.post(f"/workspaces/invitations/{str(token)}/accept")
    assert response.status_code == 200, response.text


async def test_accept_workspace_invitation_400_bad_request_invalid_token(client):
    user = await f.create_user()
    client.login(user)
    response = await client.post("/workspaces/invitations/invalid-token/accept")
    assert response.status_code == 400, response.text


async def test_accept_workspace_invitation_403_forbidden(client):
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(id=111)
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    client.login(user)
    response = await client.post(f"/workspaces/invitations/{str(token)}/accept")
    assert response.status_code == 403, response.text


async def test_accept_workspace_invitation_404_not_found_token(client):
    user = await f.create_user()
    invitation = f.build_workspace_invitation(id=111)
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    client.login(user)
    response = await client.post(f"/workspaces/invitations/{str(token)}/accept")
    assert response.status_code == 404, response.text

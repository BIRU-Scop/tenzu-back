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
from permissions.choices import WorkspacePermissions
from tests.utils import factories as f
from tests.utils.bad_params import INVALID_B64ID, NOT_EXISTING_B64ID
from workspaces.invitations.tokens import WorkspaceInvitationToken

pytestmark = pytest.mark.django_db


##########################################################
# POST /workspaces/<id>/invitations
##########################################################


async def test_create_workspace_invitations_200_ok(client):
    invitee1 = await f.create_user(email="invitee1@tenzu.demo", username="invitee1")
    await f.create_user(email="invitee2@tenzu.demo", username="invitee2")
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    owner_role = next(filter(attrgetter("is_owner"), roles))
    member_role = next(filter(lambda role: role.slug == "member", roles))
    data = {
        "invitations": [
            {"email": "invitee2@tenzu.demo", "role_id": owner_role.b64id},
            {"email": "test@email.com", "role_id": member_role.b64id},
            {"username": invitee1.username, "role_id": member_role.b64id},
        ]
    }
    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 200, response.data

    user = await f.create_user()
    client.login(user)
    role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.CREATE_MODIFY_MEMBER], workspace=workspace
    )
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 200, response.data


async def test_create_workspace_invitations_owner_no_permission(
    client,
):
    invitee1 = await f.create_user(email="invitee1@tenzu.demo", username="invitee1")
    await f.create_user(email="invitee2@tenzu.demo", username="invitee2")
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    owner_role = next(filter(attrgetter("is_owner"), roles))
    member_role = next(filter(lambda role: role.slug == "member", roles))
    existing_invitation = await f.create_workspace_invitation(
        workspace=workspace, role__is_owner=True
    )
    membership = await f.create_workspace_membership(workspace=workspace)
    data = {
        "invitations": [
            {"email": "invitee2@tenzu.demo", "role_id": owner_role.b64id},
            {"email": "test@email.com", "role_id": member_role.b64id},
            {"username": invitee1.username, "role_id": member_role.b64id},
            {
                "username": existing_invitation.user.username,
                "role_id": member_role.b64id,
            },
        ]
    }
    client.login(membership.user)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 403, response.data
    detail = response.json()["detail"]
    assert (
        existing_invitation.user.username in detail and "invitee2@tenzu.demo" in detail
    )


async def test_create_workspace_invitations_400_bad_request_not_existing_username(
    client,
):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    owner_role = next(filter(attrgetter("is_owner"), roles))
    data = {
        "invitations": [{"username": "not-a-username", "role_id": owner_role.b64id}]
    }
    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 400, response.data


async def test_create_workspace_invitations_non_existing_role(client):
    workspace = await f.create_workspace()
    data = {
        "invitations": [
            {"email": "test@email.com", "role_id": NOT_EXISTING_B64ID},
        ]
    }
    client.login(workspace.created_by)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 400, response.data


async def test_create_workspace_invitations_401_not_authorised_anonymous_user(client):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    owner_role = next(filter(attrgetter("is_owner"), roles))
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_id": owner_role.b64id},
            {"email": "test@email.com", "role_id": owner_role.b64id},
        ]
    }
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 401, response.data


async def test_create_workspace_invitations_403_forbidden_user_without_permission(
    client,
):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    owner_role = next(filter(attrgetter("is_owner"), roles))
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_id": owner_role.b64id},
            {"email": "test@email.com", "role_id": owner_role.b64id},
        ]
    }
    user = await f.create_user()
    client.login(user)
    response = await client.post(
        f"/workspaces/{workspace.b64id}/invitations", json=data
    )
    assert response.status_code == 403, response.data


async def test_create_workspace_invitations_404_not_found_workspace_b64id(client):
    user = await f.create_user()
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_id": NOT_EXISTING_B64ID},
            {"email": "test@email.com", "role_id": NOT_EXISTING_B64ID},
        ]
    }
    client.login(user)
    response = await client.post(
        f"/workspaces/{NOT_EXISTING_B64ID}/invitations", json=data
    )
    assert response.status_code == 404, response.data


async def test_create_workspace_invitations_422_unprocessable_workspace_b64id(client):
    user = await f.create_user()
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_id": NOT_EXISTING_B64ID},
            {"email": "test@email.com", "role_id": NOT_EXISTING_B64ID},
        ]
    }
    client.login(user)
    response = await client.post(f"/workspaces/{INVALID_B64ID}/invitations", json=data)
    assert response.status_code == 422, response.data


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
    assert response.status_code == 200, response.data
    assert len(response.json()) == 4

    user = await f.create_user()
    client.login(user)
    role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.CREATE_MODIFY_MEMBER], workspace=workspace
    )
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    response = await client.get(f"/workspaces/{workspace.b64id}/invitations")
    assert response.status_code == 200, response.data


async def test_list_workspaces_invitations_403_forbidden_no_permissions(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/workspaces/{workspace.b64id}/invitations")
    assert response.status_code == 403, response.data
    role = await f.create_workspace_role(permissions=[], workspace=workspace)
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    response = await client.get(f"/workspaces/{workspace.b64id}/invitations")
    assert response.status_code == 403, response.data


async def test_list_workspaces_404_not_found_workspace_b64id(client):
    workspace = await f.create_workspace()
    client.login(workspace.created_by)
    response = await client.get(f"/workspaces/{NOT_EXISTING_B64ID}/invitations")
    assert response.status_code == 404, response.data


async def test_list_workspaces_422_unprocessable_workspace_b64id(client):
    workspace = await f.create_workspace()
    client.login(workspace.created_by)
    offset = 0
    limit = 1
    response = await client.get(
        f"/workspaces/{INVALID_B64ID}/invitations?offset={offset}&limit={limit}"
    )
    assert response.status_code == 422, response.data


#########################################################################
# GET /workspaces/invitations/by_token/<token>
#########################################################################


async def test_get_workspace_invitation_200_ok(client):
    invitation = await f.create_workspace_invitation()
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    response = await client.get(f"/workspaces/invitations/by_token/{str(token)}")
    assert response.status_code == 200, response.data


async def test_get_workspace_invitation_400_bad_request_invalid_token(client):
    response = await client.get("/workspaces/invitations/by_token/invalid-token")
    assert response.status_code == 400, response.data


async def test_get_workspace_invitation_404_not_found_token(client):
    invitation = f.build_workspace_invitation(id=111)
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    response = await client.get(f"/workspaces/invitations/by_token/{str(token)}")
    assert response.status_code == 404, response.data


async def test_get_workspace_invitation_revoked_does_not_exist(client):
    invitation = await f.create_workspace_invitation(status=InvitationStatus.REVOKED)
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    response = await client.get(f"/workspaces/invitations/by_token/{str(token)}")
    assert response.status_code == 404, response.data


#########################################################################
# POST /workspaces/invitations/by_token/<token>/accept
#########################################################################


async def test_accept_workspace_invitation_200_ok(client):
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(email=user.email)
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    client.login(user)
    response = await client.post(
        f"/workspaces/invitations/by_token/{str(token)}/accept"
    )
    assert response.status_code == 200, response.data


async def test_accept_workspace_invitation_400_bad_request_invalid_token(client):
    user = await f.create_user()
    client.login(user)
    response = await client.post(
        "/workspaces/invitations/by_token/invalid-token/accept"
    )
    assert response.status_code == 400, response.data


async def test_accept_workspace_invitation_403_forbidden(client):
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(id=111)
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    client.login(user)
    response = await client.post(
        f"/workspaces/invitations/by_token/{str(token)}/accept"
    )
    assert response.status_code == 403, response.data


async def test_accept_workspace_invitation_404_not_found_token(client):
    user = await f.create_user()
    invitation = f.build_workspace_invitation(id=111)
    token = await WorkspaceInvitationToken.create_for_object(invitation)

    client.login(user)
    response = await client.post(
        f"/workspaces/invitations/by_token/{str(token)}/accept"
    )
    assert response.status_code == 404, response.data


#########################################################################
# POST /workspaces/<id>/invitations/accept authenticated user accepts a workspace invitation
#########################################################################


async def test_accept_workspace_invitations_anonymous_user(
    client,
):
    workspace = await f.create_workspace()
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/accept")
    assert response.status_code == 401, response.data


async def test_accept_user_workspace_invitation_ok(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        email=user.email,
        user=user,
        status=InvitationStatus.PENDING,
        workspace=workspace,
    )
    assert not await user.workspace_memberships.filter(
        workspace=invitation.workspace
    ).aexists()

    client.login(user)
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/accept")
    assert response.status_code == 200, response.data
    assert response.json()["user"]["username"] == user.username
    assert response.json()["email"] == user.email
    assert await user.workspace_memberships.filter(
        workspace=invitation.workspace
    ).aexists()


async def test_accept_user_workspace_not_found(
    client,
):
    workspace = await f.create_workspace()
    uninvited_user = await f.create_user()

    client.login(uninvited_user)
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/accept")
    assert response.status_code == 404, response.data


async def test_accept_user_already_accepted_workspace_invitation(
    client,
):
    workspace = await f.create_workspace()
    invited_user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        email=invited_user.email,
        user=invited_user,
        status=InvitationStatus.ACCEPTED,
        workspace=workspace,
    )
    await WorkspaceInvitationToken.create_for_object(invitation)

    client.login(invited_user)
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/accept")
    assert response.status_code == 400, response.data


async def test_accept_user_revoked_workspace_invitation(
    client,
):
    workspace = await f.create_workspace()
    invited_user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        email=invited_user.email,
        user=invited_user,
        status=InvitationStatus.REVOKED,
        workspace=workspace,
    )
    await WorkspaceInvitationToken.create_for_object(invitation)

    client.login(invited_user)
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/accept")
    assert response.status_code == 400, response.data


#########################################################################
# POST /workspaces/invitations/<id>/resend
#########################################################################


async def test_resend_workspace_invitations_anonymous_user(
    client,
):
    workspace = await f.create_workspace()
    invitation = await f.create_workspace_invitation(
        user=None, email="test@test.test", workspace=workspace
    )
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 401, response.data


async def test_resend_workspace_invitation_by_email_ok(
    client,
):
    workspace = await f.create_workspace()
    email = "user-test@email.com"
    invitation = await f.create_workspace_invitation(
        user=None, email=email, workspace=workspace
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.PENDING

    user = await f.create_user()
    client.login(user)
    role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.CREATE_MODIFY_MEMBER], workspace=workspace
    )
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    invitation = await f.create_workspace_invitation(
        user=None, email="test@demo.com", workspace=workspace
    )
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.PENDING


async def test_resend_workspace_invitation_by_user_email_ok(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        user=user, email=user.email, workspace=workspace
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.PENDING

    user = await f.create_user()
    client.login(user)
    role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.CREATE_MODIFY_MEMBER], workspace=workspace
    )
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        user=user, email=user.email, workspace=workspace
    )
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.PENDING


async def test_resend_workspace_invitation_user_without_permission(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    email = "user-test-2@email.com"
    invitation = await f.create_workspace_invitation(
        user=None, email=email, workspace=workspace
    )

    client.login(user)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 403, response.data
    role = await f.create_workspace_role(permissions=[], workspace=workspace)
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 403, response.data


async def test_resend_workspace_invitation_not_exist(
    client,
):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.post(
        f"workspaces/invitations/{NOT_EXISTING_B64ID}/resend",
    )
    assert response.status_code == 404, response.data


async def test_resend_workspace_invitation_already_accepted(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        user=user,
        email=user.email,
        workspace=workspace,
        status=InvitationStatus.ACCEPTED,
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 400, response.data


async def test_resend_workspace_invitation_revoked(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        user=user,
        email=user.email,
        workspace=workspace,
        status=InvitationStatus.REVOKED,
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 400, response.data


#########################################################################
# POST /workspaces/invitations/<id>/revoke
#########################################################################


async def test_revoke_workspace_invitations_anonymous_user(
    client,
):
    workspace = await f.create_workspace()
    invitation = await f.create_workspace_invitation(
        user=None,
        email="test@test.test",
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 401, response.data


async def test_revoke_workspace_invitation_for_email_ok(
    client,
):
    workspace = await f.create_workspace()
    email = "someone@email.com"
    invitation = await f.create_workspace_invitation(
        user=None, email=email, workspace=workspace, status=InvitationStatus.PENDING
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.REVOKED

    user = await f.create_user()
    client.login(user)
    role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.CREATE_MODIFY_MEMBER], workspace=workspace
    )
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    invitation = await f.create_workspace_invitation(
        user=None, email="test@demo.com", workspace=workspace
    )
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.REVOKED


async def test_revoke_workspace_invitation_for_user_email_ok(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        user=user,
        email=user.email,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.REVOKED

    user = await f.create_user()
    client.login(user)
    role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.CREATE_MODIFY_MEMBER], workspace=workspace
    )
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        user=user, email=user.email, workspace=workspace
    )
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.REVOKED


async def test_revoke_workspace_invitation_not_found(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()

    client.login(workspace.created_by)
    data = {"username_or_email": user.email}
    response = await client.post(
        f"workspaces/invitations/{NOT_EXISTING_B64ID}/revoke",
    )
    assert response.status_code == 404, response.data


async def test_revoke_workspace_invitation_already_member_invalid(
    client,
):
    workspace = await f.create_workspace()
    member_role = await f.create_workspace_role(
        permissions=WorkspacePermissions.values,
        is_owner=False,
        workspace=workspace,
    )
    user = await f.create_user()
    await f.create_workspace_membership(
        user=user, workspace=workspace, role=member_role
    )
    invitation = await f.create_workspace_invitation(
        user=user,
        email=user.email,
        workspace=workspace,
        status=InvitationStatus.ACCEPTED,
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 400, response.data


async def test_revoke_workspace_invitation_revoked(
    client,
):
    workspace = await f.create_workspace()
    member_role = await f.create_workspace_role(
        permissions=WorkspacePermissions.values,
        is_owner=False,
        workspace=workspace,
    )
    user = await f.create_user()
    await f.create_workspace_membership(
        user=user, workspace=workspace, role=member_role
    )
    invitation = await f.create_workspace_invitation(
        user=user,
        email=user.email,
        workspace=workspace,
        status=InvitationStatus.REVOKED,
    )

    client.login(workspace.created_by)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 400, response.data


async def test_revoke_workspace_invitation_user_without_permission(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        user=None, email=user.email, workspace=workspace
    )

    client.login(user)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 403, response.data
    role = await f.create_workspace_role(permissions=[], workspace=workspace)
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 403, response.data


async def test_revoke_workspace_invitation_owner(
    client,
):
    workspace = await f.create_workspace()
    user = await f.create_user()
    owner_role = await workspace.roles.aget(is_owner=True)
    invitation = await f.create_workspace_invitation(
        user=None, email=user.email, workspace=workspace, role=owner_role
    )
    role = await f.create_workspace_role(workspace=workspace)
    membership = await f.create_workspace_membership(
        role=role, workspace=workspace, user=user
    )

    client.login(user)
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 403, response.data
    membership.role = owner_role
    await membership.asave()
    response = await client.post(
        f"workspaces/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.REVOKED


#########################################################################
# POST /workspaces/<id>/invitations/deny
#########################################################################


async def test_deny_workspace_invitations_anonymous_user(
    client,
):
    workspace = await f.create_workspace()
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/deny")
    assert response.status_code == 401, response.data


async def test_deny_workspace_invitation_ok(
    client,
):
    user = await f.create_user()
    workspace = await f.create_workspace()
    invitation = await f.create_workspace_invitation(
        user=user, workspace=workspace, status=InvitationStatus.PENDING
    )

    client.login(user)
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/deny")
    assert response.status_code == 200, response.data
    assert response.json()["id"] == invitation.b64id


async def test_deny_workspace_invitation_not_found(
    client,
):
    workspace = await f.create_workspace()

    client.login(workspace.created_by)
    response = await client.post(f"workspaces/{NOT_EXISTING_B64ID}/invitations/deny")
    assert response.status_code == 404, response.data
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/deny")
    assert response.status_code == 404, response.data


async def test_deny_workspace_invitation_already_member_invalid(
    client,
):
    workspace = await f.create_workspace()
    member_role = await f.create_workspace_role(
        permissions=WorkspacePermissions.values,
        is_owner=False,
        workspace=workspace,
    )
    user = await f.create_user()
    await f.create_workspace_membership(
        user=user, workspace=workspace, role=member_role
    )
    await f.create_workspace_invitation(
        user=user,
        email=user.email,
        workspace=workspace,
        status=InvitationStatus.ACCEPTED,
    )

    client.login(user)
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/deny")
    assert response.status_code == 400, response.data


async def test_deny_workspace_invitation_already_denied(
    client,
):
    workspace = await f.create_workspace()
    member_role = await f.create_workspace_role(
        permissions=WorkspacePermissions.values,
        is_owner=False,
        workspace=workspace,
    )
    user = await f.create_user()
    await f.create_workspace_membership(
        user=user, workspace=workspace, role=member_role
    )
    await f.create_workspace_invitation(
        user=user,
        email=user.email,
        workspace=workspace,
        status=InvitationStatus.DENIED,
    )

    client.login(user)
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/deny")
    assert response.status_code == 400, response.data


async def test_deny_workspace_invitation_revoked(
    client,
):
    workspace = await f.create_workspace()
    member_role = await f.create_workspace_role(
        permissions=WorkspacePermissions.values,
        is_owner=False,
        workspace=workspace,
    )
    user = await f.create_user()
    await f.create_workspace_membership(
        user=user, workspace=workspace, role=member_role
    )
    await f.create_workspace_invitation(
        user=user,
        email=user.email,
        workspace=workspace,
        status=InvitationStatus.REVOKED,
    )

    client.login(user)
    response = await client.post(f"workspaces/{workspace.b64id}/invitations/deny")
    assert response.status_code == 400, response.data


##########################################################
# PATCH /workspaces/invitations/<id>
##########################################################


async def test_update_workspace_invitation_role_invitation_not_exist(
    client,
):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    owner_role = next(filter(attrgetter("is_owner"), roles))

    client.login(workspace.created_by)
    data = {"role_id": owner_role.b64id}
    response = await client.patch(
        f"workspaces/invitations/{NOT_EXISTING_B64ID}", json=data
    )
    assert response.status_code == 404, response.data


async def test_update_workspace_invitation_role_user_without_permission(
    client,
):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    member_role = next(filter(lambda role: role.slug == "member", roles))
    user = await f.create_user()

    invited_user = await f.create_user()
    invitation = await f.create_workspace_invitation(
        user=invited_user,
        workspace=workspace,
        email=invited_user.email,
    )

    client.login(user)
    data = {"role_id": member_role.b64id}
    response = await client.patch(
        f"/workspaces/invitations/{invitation.b64id}", json=data
    )
    assert response.status_code == 403, response.data
    role = await f.create_workspace_role(permissions=[], workspace=workspace)
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    response = await client.patch(
        f"/workspaces/invitations/{invitation.b64id}", json=data
    )
    assert response.status_code == 403, response.data


async def test_update_workspace_invitation_owner(
    client,
):
    user = await f.create_user()
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    owner_role = next(filter(attrgetter("is_owner"), roles))
    member_role = next(filter(lambda role: role.slug == "member", roles))
    owner_invitation = await f.create_workspace_invitation(
        user=None, email="email1@test.demo", workspace=workspace, role=owner_role
    )
    member_invitation = await f.create_workspace_invitation(
        user=None, email="email2@test.demo", workspace=workspace, role=member_role
    )
    membership = await f.create_workspace_membership(
        role=member_role, workspace=workspace, user=user
    )

    client.login(user)
    data = {"role_id": owner_role.b64id}
    response = await client.patch(
        f"/workspaces/invitations/{member_invitation.b64id}",
        json=data,
    )
    assert response.status_code == 403, response.data
    response = await client.patch(
        f"/workspaces/invitations/{owner_invitation.b64id}", json=data
    )
    assert response.status_code == 403, response.data
    membership.role = owner_role
    await membership.asave()
    response = await client.patch(
        f"/workspaces/invitations/{member_invitation.b64id}",
        json=data,
    )
    assert response.status_code == 200, response.data
    response = await client.patch(
        f"/workspaces/invitations/{owner_invitation.b64id}", json=data
    )
    assert response.status_code == 200, response.data


async def test_update_workspace_invitation_role_ok(
    client,
):
    workspace = await f.create_workspace()
    roles = list(workspace.roles.all())
    member_role = next(filter(lambda role: role.slug == "member", roles))
    readonlymember_role = next(
        filter(lambda role: role.slug == "readonly-member", roles)
    )
    user = await f.create_user()
    general_admin_role = await f.create_workspace_role(
        workspace=workspace,
        permissions=WorkspacePermissions.values,
        is_owner=False,
    )
    invitation = await f.create_workspace_invitation(
        user=user, workspace=workspace, role=general_admin_role, email=user.email
    )

    client.login(workspace.created_by)
    data = {"role_id": readonlymember_role.b64id}
    response = await client.patch(
        f"workspaces/invitations/{invitation.b64id}", json=data
    )
    assert response.status_code == 200, response.data

    user = await f.create_user()
    client.login(user)
    role = await f.create_workspace_role(
        permissions=[WorkspacePermissions.CREATE_MODIFY_MEMBER], workspace=workspace
    )
    await f.create_workspace_membership(role=role, workspace=workspace, user=user)
    data = {"role_id": member_role.b64id}
    response = await client.patch(
        f"workspaces/invitations/{invitation.b64id}", json=data
    )
    assert response.status_code == 200, response.data

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
from permissions.choices import ProjectPermissions
from projects.invitations.tokens import ProjectInvitationToken
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_B64ID

pytestmark = pytest.mark.django_db


##########################################################
# POST /projects/<id>/invitations
##########################################################


async def test_create_project_invitations_anonymous_user(client, project_template):
    project = await f.create_project(project_template)
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "member"},
        ]
    }
    response = await client.post(f"/projects/{project.b64id}/invitations", json=data)
    assert response.status_code == 401, response.data


async def test_create_project_invitations_user_without_permission(
    client, project_template
):
    project = await f.create_project(project_template)
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "member"},
        ]
    }
    user = await f.create_user()
    client.login(user)
    response = await client.post(f"/projects/{project.b64id}/invitations", json=data)
    assert response.status_code == 403, response.data


async def test_create_project_invitations_user_wrong_email_format(
    client, project_template
):
    project = await f.create_project(project_template)
    data = {
        "invitations": [
            {"email": "user-test@email", "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "member"},
        ]
    }
    user = await f.create_user()
    client.login(user)
    response = await client.post(f"/projects/{project.b64id}/invitations", json=data)
    assert response.status_code == 422, response.data


async def test_create_project_invitations_project_not_found(client):
    user = await f.create_user()
    data = {
        "invitations": [
            {"email": "user-test@email.com", "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "member"},
        ]
    }
    client.login(user)
    response = await client.post(
        f"/projects/{NOT_EXISTING_B64ID}/invitations", json=data
    )
    assert response.status_code == 404, response.data


async def test_create_project_invitations_not_existing_username(
    client, project_template
):
    project = await f.create_project(project_template)
    data = {"invitations": [{"username": "not-a-username", "role_slug": "member"}]}
    client.login(project.created_by)
    response = await client.post(f"/projects/{project.b64id}/invitations", json=data)
    assert response.status_code == 400, response.data


async def test_create_project_invitations_non_existing_role(client, project_template):
    project = await f.create_project(project_template)
    data = {
        "invitations": [
            {"email": "test@email.com", "role_slug": "non_existing_role"},
        ]
    }
    client.login(project.created_by)
    response = await client.post(f"/projects/{project.b64id}/invitations", json=data)
    assert response.status_code == 400, response.data


async def test_create_project_invitations_owner_no_permission(client, project_template):
    invitee1 = await f.create_user(email="invitee1@tenzu.demo", username="invitee1")
    await f.create_user(email="invitee2@tenzu.demo", username="invitee2")
    project = await f.create_project(project_template)
    existing_invitation = await f.create_project_invitation(
        project=project, role__is_owner=True
    )
    membership = await f.create_project_membership(project=project)
    data = {
        "invitations": [
            {"email": "invitee2@tenzu.demo", "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "member"},
            {"username": invitee1.username, "role_slug": "member"},
            {"username": existing_invitation.user.username, "role_slug": "member"},
        ]
    }
    client.login(membership.user)
    response = await client.post(f"/projects/{project.b64id}/invitations", json=data)
    assert response.status_code == 403, response.data
    detail = response.json()["detail"]
    assert (
        existing_invitation.user.username in detail and "invitee2@tenzu.demo" in detail
    )


async def test_create_project_invitations(client, project_template):
    invitee1 = await f.create_user(email="invitee1@tenzu.demo", username="invitee1")
    invitee2 = await f.create_user(email="invitee2@tenzu.demo", username="invitee2")
    project = await f.create_project(project_template)
    data = {
        "invitations": [
            {"email": invitee2.email, "role_slug": "owner"},
            {"email": "test@email.com", "role_slug": "member"},
            {"username": invitee1.username, "role_slug": "member"},
        ]
    }
    client.login(project.created_by)
    response = await client.post(f"/projects/{project.b64id}/invitations", json=data)
    assert response.status_code == 200, response.data

    user = await f.create_user()
    client.login(user)
    role = await f.create_project_role(
        permissions=[ProjectPermissions.CREATE_MODIFY_MEMBER], project=project
    )
    await f.create_project_membership(role=role, project=project, user=user)
    response = await client.post(f"/projects/{project.b64id}/invitations", json=data)
    assert response.status_code == 200, response.data


##########################################################
# LIST /projects/<id>/invitations
##########################################################


async def test_list_project_invitations_ok(client, project_template):
    project = await f.create_project(project_template)
    member_role = await project.roles.aget(slug="member")

    user1 = await f.create_user(full_name="AAA")
    await f.create_project_invitation(
        email=user1.email,
        user=user1,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    user2 = await f.create_user(full_name="BBB")
    await f.create_project_invitation(
        email=user2.email,
        user=user2,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    await f.create_project_invitation(
        email="non-existing@email.com",
        user=None,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    user = await f.create_user()
    await f.create_project_invitation(
        email=user.email,
        user=user,
        project=project,
        role=member_role,
        status=InvitationStatus.ACCEPTED,
    )

    client.login(project.created_by)

    response = await client.get(f"/projects/{project.b64id}/invitations")
    assert response.status_code == 200, response.data
    assert len(response.json()) == 4

    user = await f.create_user()
    client.login(user)
    role = await f.create_project_role(
        permissions=[ProjectPermissions.CREATE_MODIFY_MEMBER], project=project
    )
    await f.create_project_membership(role=role, project=project, user=user)
    response = await client.get(f"/projects/{project.b64id}/invitations")
    assert response.status_code == 200, response.data


async def test_list_project_invitations_not_allowed_to_public_users(
    client, project_template
):
    project = await f.create_project(project_template)
    not_a_member = await f.create_user()

    client.login(not_a_member)
    response = await client.get(f"/projects/{project.b64id}/invitations")
    assert response.status_code == 403, response.data


async def test_list_projects_invitations_403_forbidden_no_permissions(
    client, project_template
):
    project = await f.create_project(project_template)
    user = await f.create_user()
    client.login(user)
    response = await client.get(f"/projects/{project.b64id}/invitations")
    assert response.status_code == 403, response.data
    role = await f.create_project_role(permissions=[], project=project)
    await f.create_project_membership(role=role, project=project, user=user)
    response = await client.get(f"/projects/{project.b64id}/invitations")
    assert response.status_code == 403, response.data


async def test_list_project_invitations_not_allowed_to_anonymous_users(
    client, project_template
):
    project = await f.create_project(project_template)

    response = await client.get(f"/projects/{project.b64id}/invitations")
    assert response.status_code == 401, response.data


async def test_list_project_invitations_wrong_id(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.get(f"/projects/{NOT_EXISTING_B64ID}/invitations")
    assert response.status_code == 404, response.data


#########################################################################
# GET /projects/invitations/<token>
#########################################################################


async def test_get_project_invitation_ok(client):
    invitation = await f.create_project_invitation()
    token = await ProjectInvitationToken.create_for_object(invitation)

    response = await client.get(f"/projects/invitations/{str(token)}")
    assert response.status_code == 200, response.data


async def test_get_project_invitation_invalid_token(client):
    response = await client.get("/projects/invitations/invalid-token")
    assert response.status_code == 400, response.data


async def test_get_project_invitation_invitation_does_not_exist(client):
    invitation = f.build_project_invitation(id=111)
    token = await ProjectInvitationToken.create_for_object(invitation)

    response = await client.get(f"/projects/invitations/{str(token)}")
    assert response.status_code == 404, response.data


async def test_get_project_invitation_accepted_does_not_exist(client):
    invitation = await f.create_project_invitation(status=InvitationStatus.ACCEPTED)
    token = await ProjectInvitationToken.create_for_object(invitation)

    response = await client.get(f"/projects/invitations/{str(token)}")
    assert response.status_code == 404, response.data


#########################################################################
# POST /projects/invitations/<token>/accept (accept a project invitation)
#########################################################################


async def test_accept_project_invitation_ok(client):
    user = await f.create_user()
    invitation = await f.create_project_invitation(email=user.email, user=user)
    token = await ProjectInvitationToken.create_for_object(invitation)
    assert not await user.project_memberships.filter(
        project=invitation.project
    ).aexists()
    assert not await user.workspace_memberships.filter(
        workspace=invitation.project.workspace
    ).aexists()

    client.login(user)
    response = await client.post(f"/projects/invitations/{str(token)}/accept")
    assert response.status_code == 200, response.data
    assert (
        await user.project_memberships.filter(project=invitation.project)
        .select_related("role")
        .aget()
    ).role == invitation.role
    workspace_membership = (
        await user.workspace_memberships.filter(workspace=invitation.project.workspace)
        .select_related("role")
        .aget()
    )
    assert not workspace_membership.role.is_owner
    assert workspace_membership.role.slug == "readonly-member"


async def test_accept_project_invitation_ok_pending_workspace_invitation(client):
    user = await f.create_user()
    invitation = await f.create_project_invitation(email=user.email, user=user)
    ws_invitation = await f.create_workspace_invitation(
        email=user.email, user=user, workspace=invitation.project.workspace
    )
    token = await ProjectInvitationToken.create_for_object(invitation)
    assert not await user.project_memberships.filter(
        project=invitation.project
    ).aexists()
    assert not await user.workspace_memberships.filter(
        workspace=invitation.project.workspace
    ).aexists()

    client.login(user)
    response = await client.post(f"/projects/invitations/{str(token)}/accept")
    assert response.status_code == 200, response.data
    assert (
        await user.project_memberships.filter(project=invitation.project)
        .select_related("role")
        .aget()
    ).role == invitation.role
    workspace_membership = (
        await user.workspace_memberships.filter(workspace=invitation.project.workspace)
        .select_related("role")
        .aget()
    )
    assert not workspace_membership.role.is_owner
    assert workspace_membership.role.slug != "readonly-member"
    assert workspace_membership.role == ws_invitation.role


async def test_accept_project_invitation_ok_already_workspace_member(client):
    user = await f.create_user()
    invitation = await f.create_project_invitation(email=user.email, user=user)
    member_role = await f.create_workspace_role(
        workspace=invitation.project.workspace,
        permissions=[],
        is_owner=False,
    )
    await f.create_workspace_membership(
        user=user, workspace=invitation.project.workspace, role=member_role
    )
    token = await ProjectInvitationToken.create_for_object(invitation)
    assert not await user.project_memberships.filter(
        project=invitation.project
    ).aexists()

    client.login(user)
    response = await client.post(f"/projects/invitations/{str(token)}/accept")
    assert response.status_code == 200, response.data
    assert (
        await user.project_memberships.filter(project=invitation.project)
        .select_related("role")
        .aget()
    ).role == invitation.role
    workspace_membership = (
        await user.workspace_memberships.filter(workspace=invitation.project.workspace)
        .select_related("role")
        .aget()
    )
    assert not workspace_membership.role.is_owner
    assert workspace_membership.role.slug != "readonly-member"
    assert workspace_membership.role == member_role


async def test_accept_project_invitation_error_invitation_invalid_token(client):
    user = await f.create_user()
    client.login(user)
    response = await client.post("/projects/invitations/invalid-token/accept")
    assert response.status_code == 400, response.data


async def test_accept_project_invitation_error_invitation_does_not_exist(client):
    user = await f.create_user()
    invitation = f.build_project_invitation(id=111)
    token = await ProjectInvitationToken.create_for_object(invitation)

    client.login(user)
    response = await client.post(f"/projects/invitations/{str(token)}/accept")
    assert response.status_code == 404, response.data


async def test_accept_project_invitation_error_user_has_no_permission_over_this_invitation(
    client,
):
    user = await f.create_user()
    invitation = await f.create_project_invitation(user=await f.create_user())
    token = await ProjectInvitationToken.create_for_object(invitation)

    client.login(user)
    response = await client.post(f"/projects/invitations/{str(token)}/accept")
    assert response.status_code == 403, response.data


async def test_accept_project_invitation_error_invitation_already_accepted(client):
    user = await f.create_user()
    invitation = await f.create_project_invitation(
        email=user.email, status=InvitationStatus.ACCEPTED
    )
    token = await ProjectInvitationToken.create_for_object(invitation)

    client.login(user)
    response = await client.post(f"/projects/invitations/{str(token)}/accept")
    assert response.status_code == 400, response.data


async def test_accept_project_invitation_error_invitation_revoked(client):
    user = await f.create_user()
    invitation = await f.create_project_invitation(
        email=user.email, status=InvitationStatus.REVOKED
    )
    token = await ProjectInvitationToken.create_for_object(invitation)

    client.login(user)
    response = await client.post(f"/projects/invitations/{str(token)}/accept")
    assert response.status_code == 400, response.data


#########################################################################
# POST /projects/<id>/invitations/accept authenticated user accepts a project invitation
#########################################################################


async def test_accept_project_invitations_anonymous_user(client, project_template):
    project = await f.create_project(project_template)
    response = await client.post(f"projects/{project.b64id}/invitations/accept")
    assert response.status_code == 401, response.data


async def test_accept_user_project_invitation_ok(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    invitation = await f.create_project_invitation(
        email=user.email,
        user=user,
        status=InvitationStatus.PENDING,
        project=project,
    )
    assert not await user.workspace_memberships.filter(
        workspace=invitation.project.workspace
    ).aexists()

    client.login(user)
    response = await client.post(f"projects/{project.b64id}/invitations/accept")
    assert response.status_code == 200, response.data
    assert response.json()["user"]["username"] == user.username
    assert response.json()["email"] == user.email
    assert await user.workspace_memberships.filter(
        workspace=invitation.project.workspace
    ).aexists()


async def test_accept_user_project_not_found(client, project_template):
    project = await f.create_project(project_template)
    uninvited_user = await f.create_user()

    client.login(uninvited_user)
    response = await client.post(f"projects/{project.b64id}/invitations/accept")
    assert response.status_code == 404, response.data


async def test_accept_user_already_accepted_project_invitation(
    client, project_template
):
    project = await f.create_project(project_template)
    invited_user = await f.create_user()
    invitation = await f.create_project_invitation(
        email=invited_user.email,
        user=invited_user,
        status=InvitationStatus.ACCEPTED,
        project=project,
    )
    await ProjectInvitationToken.create_for_object(invitation)

    client.login(invited_user)
    response = await client.post(f"projects/{project.b64id}/invitations/accept")
    assert response.status_code == 400, response.data


async def test_accept_user_revoked_project_invitation(client, project_template):
    project = await f.create_project(project_template)
    invited_user = await f.create_user()
    invitation = await f.create_project_invitation(
        email=invited_user.email,
        user=invited_user,
        status=InvitationStatus.REVOKED,
        project=project,
    )
    await ProjectInvitationToken.create_for_object(invitation)

    client.login(invited_user)
    response = await client.post(f"projects/{project.b64id}/invitations/accept")
    assert response.status_code == 400, response.data


#########################################################################
# POST /projects/<id>/invitations/resend
#########################################################################


async def test_resend_project_invitations_anonymous_user(client, project_template):
    project = await f.create_project(project_template)
    invitation = await f.create_project_invitation(
        user=None, email="test@test.test", project=project
    )
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 401, response.data


async def test_resend_project_invitation_by_email_ok(client, project_template):
    project = await f.create_project(project_template)
    email = "user-test@email.com"
    invitation = await f.create_project_invitation(
        user=None, email=email, project=project
    )

    client.login(project.created_by)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.PENDING

    user = await f.create_user()
    client.login(user)
    role = await f.create_project_role(
        permissions=[ProjectPermissions.CREATE_MODIFY_MEMBER], project=project
    )
    await f.create_project_membership(role=role, project=project, user=user)
    invitation = await f.create_project_invitation(
        user=None, email="test@demo.com", project=project
    )
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.PENDING


async def test_resend_project_invitation_by_user_email_ok(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    invitation = await f.create_project_invitation(
        user=user, email=user.email, project=project
    )

    client.login(project.created_by)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.PENDING

    user = await f.create_user()
    client.login(user)
    role = await f.create_project_role(
        permissions=[ProjectPermissions.CREATE_MODIFY_MEMBER], project=project
    )
    await f.create_project_membership(role=role, project=project, user=user)
    user = await f.create_user()
    invitation = await f.create_project_invitation(
        user=user, email=user.email, project=project
    )
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.PENDING


async def test_resend_project_invitation_user_without_permission(
    client, project_template
):
    project = await f.create_project(project_template)
    user = await f.create_user()
    email = "user-test-2@email.com"
    invitation = await f.create_project_invitation(
        user=None, email=email, project=project
    )

    client.login(user)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 403, response.data
    role = await f.create_project_role(permissions=[], project=project)
    await f.create_project_membership(role=role, project=project, user=user)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 403, response.data


async def test_resend_project_invitation_not_exist(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{NOT_EXISTING_B64ID}/resend",
    )
    assert response.status_code == 404, response.data


async def test_resend_project_invitation_already_accepted(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    invitation = await f.create_project_invitation(
        user=user,
        email=user.email,
        project=project,
        status=InvitationStatus.ACCEPTED,
    )

    client.login(project.created_by)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 400, response.data


async def test_resend_project_invitation_revoked(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    invitation = await f.create_project_invitation(
        user=user,
        email=user.email,
        project=project,
        status=InvitationStatus.REVOKED,
    )

    client.login(project.created_by)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/resend",
    )
    assert response.status_code == 400, response.data


#########################################################################
# POST /projects/<id>/invitations/revoke
#########################################################################


async def test_revoke_project_invitations_anonymous_user(client, project_template):
    project = await f.create_project(project_template)
    invitation = await f.create_project_invitation(
        user=None,
        email="test@test.test",
        project=project,
        status=InvitationStatus.PENDING,
    )
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 401, response.data


async def test_revoke_project_invitation_for_email_ok(client, project_template):
    project = await f.create_project(project_template)
    email = "someone@email.com"
    invitation = await f.create_project_invitation(
        user=None, email=email, project=project, status=InvitationStatus.PENDING
    )

    client.login(project.created_by)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.REVOKED

    user = await f.create_user()
    client.login(user)
    role = await f.create_project_role(
        permissions=[ProjectPermissions.CREATE_MODIFY_MEMBER], project=project
    )
    await f.create_project_membership(role=role, project=project, user=user)
    invitation = await f.create_project_invitation(
        user=None, email="test@demo.com", project=project
    )
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.REVOKED


async def test_revoke_project_invitation_for_user_email_ok(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    invitation = await f.create_project_invitation(
        user=user,
        email=user.email,
        project=project,
        status=InvitationStatus.PENDING,
    )

    client.login(project.created_by)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.REVOKED

    user = await f.create_user()
    client.login(user)
    role = await f.create_project_role(
        permissions=[ProjectPermissions.CREATE_MODIFY_MEMBER], project=project
    )
    await f.create_project_membership(role=role, project=project, user=user)
    user = await f.create_user()
    invitation = await f.create_project_invitation(
        user=user, email=user.email, project=project
    )
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.REVOKED


async def test_revoke_project_invitation_not_found(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()

    client.login(project.created_by)
    data = {"username_or_email": user.email}
    response = await client.post(
        f"projects/{project.b64id}/invitations/{NOT_EXISTING_B64ID}/revoke",
    )
    assert response.status_code == 404, response.data


async def test_revoke_project_invitation_already_member_invalid(
    client, project_template
):
    project = await f.create_project(project_template)
    member_role = await f.create_project_role(
        permissions=ProjectPermissions.values,
        is_owner=False,
        project=project,
    )
    user = await f.create_user()
    await f.create_project_membership(user=user, project=project, role=member_role)
    invitation = await f.create_project_invitation(
        user=user,
        email=user.email,
        project=project,
        status=InvitationStatus.ACCEPTED,
    )

    client.login(project.created_by)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 400, response.data


async def test_revoke_project_invitation_revoked(client, project_template):
    project = await f.create_project(project_template)
    member_role = await f.create_project_role(
        permissions=ProjectPermissions.values,
        is_owner=False,
        project=project,
    )
    user = await f.create_user()
    await f.create_project_membership(user=user, project=project, role=member_role)
    invitation = await f.create_project_invitation(
        user=user,
        email=user.email,
        project=project,
        status=InvitationStatus.REVOKED,
    )

    client.login(project.created_by)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 400, response.data


async def test_revoke_project_invitation_user_without_permission(
    client, project_template
):
    project = await f.create_project(project_template)
    user = await f.create_user()
    invitation = await f.create_project_invitation(
        user=None, email=user.email, project=project
    )

    client.login(user)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 403, response.data
    role = await f.create_project_role(permissions=[], project=project)
    await f.create_project_membership(role=role, project=project, user=user)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 403, response.data


async def test_revoke_project_invitation_owner(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    owner_role = await project.roles.aget(is_owner=True)
    invitation = await f.create_project_invitation(
        user=None, email=user.email, project=project, role=owner_role
    )
    role = await f.create_project_role(project=project)
    membership = await f.create_project_membership(
        role=role, project=project, user=user
    )

    client.login(user)
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 403, response.data
    membership.role = owner_role
    await membership.asave()
    response = await client.post(
        f"projects/{project.b64id}/invitations/{invitation.b64id}/revoke",
    )
    assert response.status_code == 200, response.data
    res = response.json()
    assert res["status"] == InvitationStatus.REVOKED


#########################################################################
# POST /projects/<id>/invitations/deny
#########################################################################


async def test_deny_project_invitations_anonymous_user(client, project_template):
    project = await f.create_project(project_template)
    response = await client.post(f"projects/{project.b64id}/invitations/deny")
    assert response.status_code == 401, response.data


async def test_deny_project_invitation_ok(client, project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)
    invitation = await f.create_project_invitation(
        user=user, project=project, status=InvitationStatus.PENDING
    )

    client.login(user)
    response = await client.post(f"projects/{project.b64id}/invitations/deny")
    assert response.status_code == 200, response.data
    assert response.json()["id"] == invitation.b64id


async def test_deny_project_invitation_not_found(client, project_template):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    response = await client.post(f"projects/{NOT_EXISTING_B64ID}/invitations/deny")
    assert response.status_code == 404, response.data
    response = await client.post(f"projects/{project.b64id}/invitations/deny")
    assert response.status_code == 404, response.data


async def test_deny_project_invitation_already_member_invalid(client, project_template):
    project = await f.create_project(project_template)
    member_role = await f.create_project_role(
        permissions=ProjectPermissions.values,
        is_owner=False,
        project=project,
    )
    user = await f.create_user()
    await f.create_project_membership(user=user, project=project, role=member_role)
    await f.create_project_invitation(
        user=user,
        email=user.email,
        project=project,
        status=InvitationStatus.ACCEPTED,
    )

    client.login(user)
    response = await client.post(f"projects/{project.b64id}/invitations/deny")
    assert response.status_code == 400, response.data


async def test_deny_project_invitation_already_denied(client, project_template):
    project = await f.create_project(project_template)
    member_role = await f.create_project_role(
        permissions=ProjectPermissions.values,
        is_owner=False,
        project=project,
    )
    user = await f.create_user()
    await f.create_project_membership(user=user, project=project, role=member_role)
    await f.create_project_invitation(
        user=user,
        email=user.email,
        project=project,
        status=InvitationStatus.DENIED,
    )

    client.login(user)
    response = await client.post(f"projects/{project.b64id}/invitations/deny")
    assert response.status_code == 400, response.data


async def test_deny_project_invitation_revoked(client, project_template):
    project = await f.create_project(project_template)
    member_role = await f.create_project_role(
        permissions=ProjectPermissions.values,
        is_owner=False,
        project=project,
    )
    user = await f.create_user()
    await f.create_project_membership(user=user, project=project, role=member_role)
    await f.create_project_invitation(
        user=user,
        email=user.email,
        project=project,
        status=InvitationStatus.REVOKED,
    )

    client.login(user)
    response = await client.post(f"projects/{project.b64id}/invitations/deny")
    assert response.status_code == 400, response.data


##########################################################
# PATCH /projects/<project_id>/invitations/<id>
##########################################################


async def test_update_project_invitation_role_invitation_not_exist(
    client, project_template
):
    project = await f.create_project(project_template)

    client.login(project.created_by)
    data = {"role_slug": "owner"}
    response = await client.patch(
        f"projects/{project.b64id}/invitations/{NOT_EXISTING_B64ID}", json=data
    )
    assert response.status_code == 404, response.data


async def test_update_project_invitation_role_user_without_permission(
    client, project_template
):
    project = await f.create_project(project_template)
    user = await f.create_user()

    invited_user = await f.create_user()
    invitation = await f.create_project_invitation(
        user=invited_user,
        project=project,
        email=invited_user.email,
    )

    client.login(user)
    data = {"role_slug": "member"}
    response = await client.patch(
        f"/projects/{project.b64id}/invitations/{invitation.b64id}", json=data
    )
    assert response.status_code == 403, response.data
    role = await f.create_project_role(permissions=[], project=project)
    await f.create_project_membership(role=role, project=project, user=user)
    response = await client.patch(
        f"/projects/{project.b64id}/invitations/{invitation.b64id}", json=data
    )
    assert response.status_code == 403, response.data


async def test_update_project_invitation_owner(client, project_template):
    user = await f.create_user()
    project = await f.create_project(project_template)
    owner_role = await project.roles.aget(is_owner=True)
    member_role = await project.roles.filter(is_owner=False).afirst()
    owner_invitation = await f.create_project_invitation(
        user=None, email="email1@test.demo", project=project, role=owner_role
    )
    member_invitation = await f.create_project_invitation(
        user=None, email="email2@test.demo", project=project, role=member_role
    )
    membership = await f.create_project_membership(
        role=member_role, project=project, user=user
    )

    client.login(user)
    data = {"role_slug": "owner"}
    response = await client.patch(
        f"/projects/{project.b64id}/invitations/{member_invitation.b64id}", json=data
    )
    assert response.status_code == 403, response.data
    response = await client.patch(
        f"/projects/{project.b64id}/invitations/{owner_invitation.b64id}", json=data
    )
    assert response.status_code == 403, response.data
    membership.role = owner_role
    await membership.asave()
    response = await client.patch(
        f"/projects/{project.b64id}/invitations/{member_invitation.b64id}", json=data
    )
    assert response.status_code == 200, response.data
    response = await client.patch(
        f"/projects/{project.b64id}/invitations/{owner_invitation.b64id}", json=data
    )
    assert response.status_code == 200, response.data


async def test_update_project_invitation_role_ok(client, project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    member_role = await f.create_project_role(
        project=project,
        permissions=ProjectPermissions.values,
        is_owner=False,
    )
    invitation = await f.create_project_invitation(
        user=user, project=project, role=member_role, email=user.email
    )

    client.login(project.created_by)
    data = {"role_slug": "readonly-member"}
    response = await client.patch(
        f"projects/{project.b64id}/invitations/{invitation.b64id}", json=data
    )
    assert response.status_code == 200, response.data

    user = await f.create_user()
    client.login(user)
    role = await f.create_project_role(
        permissions=[ProjectPermissions.CREATE_MODIFY_MEMBER], project=project
    )
    await f.create_project_membership(role=role, project=project, user=user)
    data = {"role_slug": "member"}
    response = await client.patch(
        f"projects/{project.b64id}/invitations/{invitation.b64id}", json=data
    )
    assert response.status_code == 200, response.data

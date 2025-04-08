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

import uuid

import pytest

from memberships.choices import InvitationStatus
from tests.utils import factories as f
from workspaces.invitations import repositories
from workspaces.invitations.models import WorkspaceInvitation

pytestmark = pytest.mark.django_db


##########################################################
# create_workspace_invitations
##########################################################


async def test_create_workspace_invitations():
    user = await f.create_user()
    user2 = await f.create_user()
    workspace = await f.create_workspace()
    role = await f.create_workspace_role(workspace=workspace)
    objs = [
        f.build_workspace_invitation(
            user=user2,
            workspace=workspace,
            email=user2.email,
            invited_by=user,
            role=role,
        ),
        f.build_workspace_invitation(
            user=None,
            workspace=workspace,
            email="test@email.com",
            invited_by=user,
            role=role,
        ),
    ]

    response = await repositories.create_invitations(WorkspaceInvitation, objs=objs)

    assert len(response) == 2


##########################################################
# list_workspace_invitations
##########################################################


async def test_list_workspace_invitations_all_pending_users():
    workspace = await f.create_workspace()
    user_a = await f.create_user(full_name="A", email="a@user.com")
    user_b = await f.create_user(full_name="B", email="b@user.com")
    email_a = user_a.email
    email_b = user_b.email
    email_x = "x@notauser.com"
    email_y = "y@notauser.com"
    email_z = "z@notauser.com"

    await f.create_workspace_invitation(
        email=email_a,
        user=user_a,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )
    await f.create_workspace_invitation(
        email=email_b,
        user=user_b,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )
    await f.create_workspace_invitation(
        email=email_z,
        user=None,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )
    await f.create_workspace_invitation(
        email=email_x,
        user=None,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )
    await f.create_workspace_invitation(
        email=email_y,
        user=None,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )
    user = await f.create_user()
    await f.create_workspace_invitation(
        email=user.email,
        user=user,
        workspace=workspace,
        status=InvitationStatus.ACCEPTED,
    )

    response = await repositories.list_invitations(
        WorkspaceInvitation,
        filters={
            "workspace_id": workspace.id,
            "status": InvitationStatus.PENDING,
        },
    )
    assert len(response) == 5
    assert response[0].email == user_a.email
    assert response[1].email == user_b.email
    assert response[2].email == email_x
    assert response[3].email == email_y
    assert response[4].email == email_z


async def test_list_workspace_invitations_single_pending_user():
    workspace = await f.create_workspace()

    user1 = await f.create_user(full_name="AAA")
    await f.create_workspace_invitation(
        email=user1.email,
        user=user1,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )
    await f.create_workspace_invitation(
        email="non-existing@email.com",
        user=None,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )

    response = await repositories.list_invitations(
        WorkspaceInvitation,
        filters={
            "workspace_id": workspace.id,
            "user": user1,
            "status": InvitationStatus.PENDING,
        },
    )
    assert len(response) == 1
    assert response[0].email == user1.email


async def test_list_workspace_invitations_single_pending_non_existing_user():
    workspace = await f.create_workspace()

    non_existing_email = "non-existing@email.com"
    await f.create_workspace_invitation(
        email=non_existing_email,
        user=None,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )

    invitations = await repositories.list_invitations(
        WorkspaceInvitation,
        filters={
            "workspace_id": workspace.id,
            "email": non_existing_email,
            "status": InvitationStatus.PENDING,
        },
    )
    assert len(invitations) == 1
    assert invitations[0].email == non_existing_email


async def test_list_workspace_invitations_all_accepted_users():
    workspace = await f.create_workspace()

    user1 = await f.create_user(full_name="AAA")
    await f.create_workspace_invitation(
        email=user1.email,
        user=user1,
        workspace=workspace,
        status=InvitationStatus.ACCEPTED,
    )

    response = await repositories.list_invitations(
        WorkspaceInvitation,
        filters={
            "workspace_id": workspace.id,
            "status": InvitationStatus.ACCEPTED,
        },
    )
    assert len(response) == 1
    assert response[0].email == user1.email


##########################################################
# get_workspace_invitation
##########################################################


async def test_get_workspace_invitation_ok() -> None:
    invitation = await f.create_workspace_invitation()

    new_invitation = await repositories.get_invitation(
        WorkspaceInvitation, filters={"id": invitation.id}
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def test_get_workspace_invitation_not_found() -> None:
    with pytest.raises(WorkspaceInvitation.DoesNotExist):
        await repositories.get_invitation(WorkspaceInvitation, filters={"id": 1001})


async def test_get_workspace_invitation_by_user_username() -> None:
    invitation = await f.create_workspace_invitation()

    new_invitation = await repositories.get_invitation(
        WorkspaceInvitation,
        filters={
            "workspace_id": invitation.workspace.id,
            "status__in": [InvitationStatus.PENDING],
        },
        q_filter=repositories.username_or_email_query(invitation.user.username),
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def test_get_workspace_invitation_by_user_email() -> None:
    invitation = await f.create_workspace_invitation()

    new_invitation = await repositories.get_invitation(
        WorkspaceInvitation,
        filters={
            "workspace_id": invitation.workspace.id,
            "status__in": [InvitationStatus.PENDING],
        },
        q_filter=repositories.username_or_email_query(invitation.user.email),
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def test_get_workspace_invitation_by_email() -> None:
    invitation = await f.create_workspace_invitation(user=None)

    new_invitation = await repositories.get_invitation(
        WorkspaceInvitation,
        filters={
            "workspace_id": invitation.workspace.id,
            "status__in": [InvitationStatus.PENDING],
        },
        q_filter=repositories.username_or_email_query(invitation.email),
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def test_get_workspace_invitation_by_email_no_user() -> None:
    invitation = await f.create_workspace_invitation(user=None)

    new_invitation = await repositories.get_invitation(
        WorkspaceInvitation,
        filters={
            "workspace_id": invitation.workspace.id,
        },
        q_filter=repositories.username_or_email_query(invitation.email),
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def test_get_workspace_invitation_by_id() -> None:
    invitation = await f.create_workspace_invitation()

    new_invitation = await repositories.get_invitation(
        WorkspaceInvitation, filters={"id": invitation.id}
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def get_workspace_invitation_by_id_not_found() -> None:
    with pytest.raises(WorkspaceInvitation.DoesNotExist):
        await repositories.get_invitation(
            WorkspaceInvitation, filters={"id": uuid.uuid1()}
        )


async def test_exist_workspace_invitation() -> None:
    user = await f.create_user()

    assert not await repositories.exists_invitation(
        WorkspaceInvitation,
        {
            "user": user,
        },
    )
    invitation = await f.create_workspace_invitation(
        email=user.email,
        user=user,
    )

    assert await repositories.exists_invitation(
        WorkspaceInvitation,
        {
            "user": user,
        },
    )


##########################################################
# update_workspace_invitations
##########################################################


async def test_update_workspace_invitation():
    workspace = await f.create_workspace()
    user = await f.create_user()
    old_status = InvitationStatus.PENDING
    new_status = InvitationStatus.ACCEPTED

    invitation = await f.create_workspace_invitation(
        user=user, email=user.email, workspace=workspace, status=old_status
    )
    updated_invitation = await repositories.update_invitation(
        invitation=invitation,
        values={"status": new_status},
    )
    assert updated_invitation.status == new_status


async def test_bulk_update_workspace_invitations():
    workspace = await f.create_workspace()
    invitation1 = await f.create_workspace_invitation(
        workspace=workspace, num_emails_sent=1
    )
    invitation2 = await f.create_workspace_invitation(
        workspace=workspace, num_emails_sent=1
    )

    invitation1.num_emails_sent = 2
    invitation2.num_emails_sent = 3
    objs = [invitation1, invitation2]
    fields_to_update = ["num_emails_sent"]

    await repositories.bulk_update_invitations(
        WorkspaceInvitation, objs_to_update=objs, fields_to_update=fields_to_update
    )

    updated_invitation1 = await repositories.get_invitation(
        WorkspaceInvitation, filters={"id": invitation1.id}
    )
    assert updated_invitation1.num_emails_sent == 2

    updated_invitation2 = await repositories.get_invitation(
        WorkspaceInvitation, filters={"id": invitation2.id}
    )
    assert updated_invitation2.num_emails_sent == 3


async def test_update_user_workspaces_invitations():
    workspace = await f.create_workspace()
    user = await f.create_user(email="some@email.com")
    invitation = await f.create_workspace_invitation(
        workspace=workspace, email="some@email.com", user=None
    )
    assert not invitation.user

    await repositories.update_user_invitations(WorkspaceInvitation, user=user)

    invitation = await repositories.get_invitation(
        WorkspaceInvitation, filters={"id": invitation.id}, select_related=["user"]
    )
    assert invitation.user == user


##########################################################
# delete_workspace_invitation
##########################################################


async def test_delete_workspace_invitation():
    workspace = await f.create_workspace()
    user = await f.create_user()
    await f.create_workspace_invitation(
        user=user,
        email=user.email,
        workspace=workspace,
        status=InvitationStatus.PENDING,
    )

    deleted_invitation = await repositories.delete_invitation(
        WorkspaceInvitation,
        filters={"workspace_id": workspace.id},
        q_filter=repositories.username_or_email_query(user.email),
    )
    assert deleted_invitation == 1

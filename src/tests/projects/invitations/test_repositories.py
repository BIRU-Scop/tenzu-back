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
from asgiref.sync import sync_to_async

from memberships.choices import InvitationStatus
from projects.invitations import repositories
from projects.invitations.models import ProjectInvitation
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID

pytestmark = pytest.mark.django_db


##########################################################
# create_project_invitations
##########################################################


async def test_create_project_invitations(project_template):
    user = await f.create_user()
    user2 = await f.create_user()
    project = await f.create_project(project_template)
    role = await f.create_project_role(project=project)
    role2 = await f.create_project_role(project=project)
    objs = [
        f.build_project_invitation(
            user=user2,
            project=project,
            role=role,
            email=user2.email,
            invited_by=user,
        ),
        f.build_project_invitation(
            user=None,
            project=project,
            role=role2,
            email="test@email.com",
            invited_by=user,
        ),
    ]

    response = await repositories.create_invitations(ProjectInvitation, objs=objs)

    assert len(response) == 2


##########################################################
# get_project_invitation
##########################################################


async def test_get_project_invitation_ok() -> None:
    invitation = await f.create_project_invitation()

    new_invitation = await repositories.get_invitation(
        ProjectInvitation, filters={"id": invitation.id}
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def test_get_project_invitation_not_found() -> None:
    with pytest.raises(ProjectInvitation.DoesNotExist):
        await repositories.get_invitation(ProjectInvitation, filters={"id": 1001})


async def test_get_project_invitation_by_user_username() -> None:
    invitation = await f.create_project_invitation()

    new_invitation = await repositories.get_invitation(
        ProjectInvitation,
        filters={
            "project_id": invitation.project.id,
            "status__in": [InvitationStatus.PENDING],
        },
        q_filter=repositories.invitation_username_or_email_query(
            invitation.user.username
        ),
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def test_get_project_invitation_by_user_email() -> None:
    invitation = await f.create_project_invitation()

    new_invitation = await repositories.get_invitation(
        ProjectInvitation,
        filters={
            "project_id": invitation.project.id,
            "status__in": [InvitationStatus.PENDING],
        },
        q_filter=repositories.invitation_username_or_email_query(invitation.user.email),
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def test_get_project_invitation_by_email() -> None:
    invitation = await f.create_project_invitation(user=None)

    new_invitation = await repositories.get_invitation(
        ProjectInvitation,
        filters={
            "project_id": invitation.project.id,
            "status__in": [InvitationStatus.PENDING],
        },
        q_filter=repositories.invitation_username_or_email_query(invitation.email),
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def test_get_project_invitation_by_email_no_status() -> None:
    invitation = await f.create_project_invitation(user=None)

    new_invitation = await repositories.get_invitation(
        ProjectInvitation,
        filters={
            "project_id": invitation.project.id,
        },
        q_filter=repositories.invitation_username_or_email_query(invitation.email),
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def test_get_project_invitation_by_id() -> None:
    invitation = await f.create_project_invitation()

    new_invitation = await repositories.get_invitation(
        ProjectInvitation, filters={"id": invitation.id}
    )

    assert new_invitation is not None
    assert new_invitation == invitation


async def get_project_invitation_by_id_not_found() -> None:
    with pytest.raises(ProjectInvitation.DoesNotExist):
        await repositories.get_invitation(
            ProjectInvitation, filters={"id": NOT_EXISTING_UUID}
        )


async def test_exist_project_invitation() -> None:
    user = await f.create_user()

    assert not await repositories.exists_invitation(
        ProjectInvitation,
        {
            "user": user,
        },
    )
    invitation = await f.create_project_invitation(
        email=user.email,
        user=user,
    )

    assert await repositories.exists_invitation(
        ProjectInvitation,
        {
            "user": user,
        },
    )


##########################################################
# list_project_invitations
##########################################################


async def test_list_project_invitations_all_pending_users(project_template):
    project = await f.create_project(project_template)
    member_role = await sync_to_async(project.roles.get)(slug="member")
    email_a = "a@user.com"
    email_b = "b@user.com"
    email_x = "x@notauser.com"
    email_y = "y@notauser.com"
    email_z = "z@notauser.com"

    user_a = await f.create_user(full_name="A", email=email_b)
    await f.create_project_invitation(
        email=email_b,
        user=user_a,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    user_b = await f.create_user(full_name="B", email=email_a)
    await f.create_project_invitation(
        email=email_a,
        user=user_b,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    await f.create_project_invitation(
        email=email_z,
        user=None,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    await f.create_project_invitation(
        email=email_x,
        user=None,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    await f.create_project_invitation(
        email=email_y,
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

    response = await repositories.list_invitations(
        ProjectInvitation,
        filters={"project_id": project.id, "status": InvitationStatus.PENDING},
        order_by=["user__full_name", "email"],
    )
    assert len(response) == 5
    assert response[0].email == user_a.email
    assert response[1].email == user_b.email
    assert response[2].email == email_x
    assert response[3].email == email_y
    assert response[4].email == email_z


async def test_list_project_invitations_pending_first(project_template):
    project = await f.create_project(project_template)
    member_role = await sync_to_async(project.roles.get)(slug="member")
    email_a = "a@user.com"
    email_b = "b@user.com"
    email_x = "x@notauser.com"
    email_y = "y@notauser.com"
    email_z = "z@notauser.com"

    user_a = await f.create_user(full_name="A", email=email_b)
    await f.create_project_invitation(
        email=email_b,
        user=user_a,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    user_b = await f.create_user(full_name="B", email=email_a)
    await f.create_project_invitation(
        email=email_a,
        user=user_b,
        project=project,
        role=member_role,
        status=InvitationStatus.ACCEPTED,
    )
    await f.create_project_invitation(
        email=email_z,
        user=None,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    await f.create_project_invitation(
        email=email_x,
        user=None,
        project=project,
        role=member_role,
        status=InvitationStatus.DENIED,
    )
    await f.create_project_invitation(
        email=email_y,
        user=None,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )

    response = await repositories.list_invitations(
        ProjectInvitation,
        filters={"project_id": project.id},
        order_by=["user__full_name", "email"],
        order_priorities={"status": InvitationStatus.PENDING},
    )
    assert len(response) == 5
    assert response[0].email == user_a.email
    assert response[1].email == email_y
    assert response[2].email == email_z
    assert response[3].email == user_b.email
    assert response[4].email == email_x


async def test_list_project_invitations_single_pending_user(project_template):
    project = await f.create_project(project_template)
    member_role = await sync_to_async(project.roles.get)(slug="member")

    user1 = await f.create_user(full_name="AAA")
    await f.create_project_invitation(
        email=user1.email,
        user=user1,
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

    response = await repositories.list_invitations(
        ProjectInvitation,
        filters={
            "project_id": project.id,
            "user": user1,
            "status": InvitationStatus.PENDING,
        },
    )
    assert len(response) == 1
    assert response[0].email == user1.email


async def test_list_project_invitations_single_pending_non_existing_user(
    project_template,
):
    project = await f.create_project(project_template)
    member_role = await sync_to_async(project.roles.get)(slug="member")

    non_existing_email = "non-existing@email.com"
    await f.create_project_invitation(
        email=non_existing_email,
        user=None,
        project=project,
        role=member_role,
        status=InvitationStatus.PENDING,
    )

    invitations = await repositories.list_invitations(
        ProjectInvitation,
        filters={
            "project_id": project.id,
            "email": non_existing_email,
            "status": InvitationStatus.PENDING,
        },
    )
    assert len(invitations) == 1
    assert invitations[0].email == non_existing_email


async def test_list_project_invitations_all_accepted_users(project_template):
    project = await f.create_project(project_template)
    member_role = await sync_to_async(project.roles.get)(slug="member")

    user1 = await f.create_user(full_name="AAA")
    await f.create_project_invitation(
        email=user1.email,
        user=user1,
        project=project,
        role=member_role,
        status=InvitationStatus.ACCEPTED,
    )
    user2 = await f.create_user(full_name="BBB")
    await f.create_project_invitation(
        email=user2.email,
        user=user2,
        project=project,
        role=member_role,
        status=InvitationStatus.ACCEPTED,
    )

    response = await repositories.list_invitations(
        ProjectInvitation,
        filters={"project_id": project.id, "status": InvitationStatus.ACCEPTED},
    )
    assert len(response) == 2
    assert response[0].email == user1.email
    assert response[1].email == user2.email


##########################################################
# update_project_invitation
##########################################################


async def test_update_project_invitation(project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    old_role = await f.create_project_role(project=project)
    invitation = await f.create_project_invitation(
        user=user,
        email=user.email,
        project=project,
        status=InvitationStatus.PENDING,
        role=old_role,
    )
    assert invitation.role == old_role

    new_role = await f.create_project_role(project=project)
    updated_invitation = await repositories.update_invitation(
        invitation=invitation,
        values={"role": new_role},
    )
    assert updated_invitation.role == new_role


async def test_bulk_update_project_invitations(project_template):
    project = await f.create_project(project_template)
    role1 = await f.create_project_role(project=project)
    invitation1 = await f.create_project_invitation(role=role1)
    invitation2 = await f.create_project_invitation(role=role1)

    assert invitation1.role == role1

    role2 = await f.create_project_role(project=invitation2.project)
    invitation1.role = role2
    invitation2.role = role2
    objs = [invitation1, invitation2]
    fields_to_update = ["role"]

    await repositories.bulk_update_invitations(
        ProjectInvitation, objs_to_update=objs, fields_to_update=fields_to_update
    )
    updated_invitation1 = await repositories.get_invitation(
        ProjectInvitation, filters={"id": invitation1.id}
    )
    assert updated_invitation1.role_id == role2.id

    updated_invitation2 = await repositories.get_invitation(
        ProjectInvitation, filters={"id": invitation2.id}
    )
    assert updated_invitation2.role_id == role2.id


##########################################################
# delete_project_invitation
##########################################################


async def test_delete_project_invitation(project_template):
    project = await f.create_project(project_template)
    user = await f.create_user()
    role = await f.create_project_role(project=project)
    await f.create_project_invitation(
        user=user,
        email=user.email,
        project=project,
        status=InvitationStatus.PENDING,
        role=role,
    )

    deleted_invitation = await repositories.delete_invitation(
        ProjectInvitation,
        filters={"project_id": project.id},
        q_filter=repositories.invitation_username_or_email_query(user.email),
    )
    assert deleted_invitation == 1

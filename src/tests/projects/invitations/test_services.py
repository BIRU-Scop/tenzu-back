# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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
from unittest.mock import patch

import pytest
from django.test import override_settings

from memberships.choices import InvitationStatus
from memberships.services import exceptions as ex
from ninja_jwt.utils import aware_utcnow
from projects.invitations import services
from projects.invitations.models import ProjectInvitation
from projects.invitations.tokens import ProjectInvitationToken
from projects.memberships.models import ProjectRole
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID
from tests.utils.utils import patch_db_transaction
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships.models import WorkspaceMembership

#######################################################
# get_project_invitation
#######################################################


async def test_get_project_invitation_ok():
    invitation = f.build_project_invitation()
    token = str(await ProjectInvitationToken.create_for_object(invitation))

    with (
        patch(
            "projects.invitations.services.invitations_repositories", autospec=True
        ) as fake_invitations_repo,
    ):
        fake_invitations_repo.get_invitation.return_value = invitation
        inv = await services.get_project_invitation_by_token(token)
        fake_invitations_repo.get_invitation.assert_awaited_once_with(
            ProjectInvitation,
            filters={"id": str(invitation.id)},
            select_related=["user", "project"],
        )
        assert inv == invitation


async def test_get_project_invitation_error_invalid_token():
    with pytest.raises(ex.BadInvitationTokenError):
        await services.get_project_invitation_by_token("invalid-token")


async def test_get_project_invitation_error_not_found():
    invitation = f.build_project_invitation()
    token = str(await ProjectInvitationToken.create_for_object(invitation))

    with (
        patch(
            "projects.invitations.services.invitations_repositories", autospec=True
        ) as fake_invitations_repo,
    ):
        fake_invitations_repo.get_invitation.side_effect = (
            ProjectInvitation.DoesNotExist
        )
        with pytest.raises(ProjectInvitation.DoesNotExist):
            await services.get_project_invitation_by_token(token)
        fake_invitations_repo.get_invitation.assert_awaited_once_with(
            ProjectInvitation,
            filters={"id": str(invitation.id)},
            select_related=["user", "project"],
        )


#######################################################
# get_public_project_invitation
#######################################################


async def test_get_public_project_invitation_ok():
    user = f.build_user(is_active=True)
    invitation = f.build_project_invitation(user=user)
    token = str(await ProjectInvitationToken.create_for_object(invitation))
    available_user_logins = ["gitlab", "password"]

    with (
        patch(
            "projects.invitations.services.invitations_repositories", autospec=True
        ) as fake_invitations_repo,
    ):
        fake_invitations_repo.get_invitation.return_value = invitation
        pub_invitation = await services.get_public_pending_project_invitation(
            token=token
        )
        fake_invitations_repo.get_invitation.assert_awaited_once_with(
            ProjectInvitation,
            filters={"id": str(invitation.id), "status": InvitationStatus.PENDING},
            select_related=["user", "project"],
        )

        assert pub_invitation.email == invitation.email
        assert pub_invitation.existing_user is True
        assert pub_invitation.project.name == invitation.project.name


async def test_get_public_project_invitation_ok_without_user():
    invitation = f.build_project_invitation(user=None)
    token = str(await ProjectInvitationToken.create_for_object(invitation))

    with (
        patch(
            "projects.invitations.services.invitations_repositories", autospec=True
        ) as fake_invitations_repo,
    ):
        fake_invitations_repo.get_invitation.return_value = invitation
        pub_invitation = await services.get_public_pending_project_invitation(token)
        fake_invitations_repo.get_invitation.assert_awaited_once_with(
            ProjectInvitation,
            filters={"id": str(invitation.id), "status": InvitationStatus.PENDING},
            select_related=["user", "project"],
        )

        assert pub_invitation.email == invitation.email
        assert pub_invitation.existing_user is False
        assert pub_invitation.project.name == invitation.project.name


async def test_get_public_project_invitation_error_invitation_not_exists():
    invitation = f.build_project_invitation(user=None)
    token = str(await ProjectInvitationToken.create_for_object(invitation))

    with patch(
        "projects.invitations.services.invitations_repositories", autospec=True
    ) as fake_invitations_repo:
        fake_invitations_repo.get_invitation.side_effect = (
            ProjectInvitation.DoesNotExist
        )
        with pytest.raises(ProjectInvitation.DoesNotExist):
            await services.get_public_pending_project_invitation(token)
        fake_invitations_repo.get_invitation.assert_awaited_once_with(
            ProjectInvitation,
            filters={"id": str(invitation.id), "status": InvitationStatus.PENDING},
            select_related=["user", "project"],
        )


#######################################################
# list_project_invitations
#######################################################


async def test_list_project_invitations_ok_admin():
    invitation = f.build_project_invitation()

    with (
        patch(
            "projects.invitations.services.invitations_repositories", autospec=True
        ) as fake_invitations_repo,
    ):
        fake_invitations_repo.list_invitations.return_value = [invitation]

        invitations = await services.list_project_invitations(
            project_id=invitation.project.id
        )

        fake_invitations_repo.list_invitations.assert_awaited_once_with(
            ProjectInvitation,
            filters={
                "project_id": invitation.project.id,
            },
            select_related=["project", "user"],
            order_by=["user__full_name", "email"],
            order_priorities={"status": InvitationStatus.PENDING},
        )
        assert invitations == [invitation]


#######################################################
# send_project_invitation_email
#######################################################


async def test_send_project_invitations_for_existing_user(tqmanager, correlation_id):
    user = f.build_user(email="user-test@email.com")
    project = f.build_project()
    role = f.build_project_role(project=project, slug="owner", is_owner=True)

    invitation = f.build_project_invitation(
        user=user,
        project=project,
        role=role,
        email=user.email,
        invited_by=project.created_by,
    )

    with patch(
        "projects.invitations.services.ProjectInvitationToken", autospec=True
    ) as FakeProjectInvitationToken:
        FakeProjectInvitationToken.create_for_object.return_value = "invitation-token"

        await services.send_project_invitation_email(
            invitation=invitation,
            project=invitation.project,
            sender=invitation.invited_by,
        )

        assert len(tqmanager.pending_jobs) == 1

        job = tqmanager.pending_jobs[0]
        assert "send_email" in job["task_name"]

        args = job["args"]
        assert args["email_name"] == "project_invitation"
        assert args["to"] == invitation.email
        assert args["lang"] == invitation.user.lang
        assert args["context"]["invitation_token"] == "invitation-token"
        assert args["context"]["project_color"] == invitation.project.color
        assert args["context"]["project_workspace"] == invitation.project.workspace.name
        assert args["context"]["project_image_url"] is None
        assert args["context"]["project_name"] == invitation.project.name
        assert args["context"]["project_id"] == invitation.project.b64id
        assert args["context"]["receiver_name"] == invitation.user.full_name
        assert args["context"]["sender_name"] == invitation.invited_by.full_name


async def test_send_project_invitations_for_new_user(tqmanager):
    project = f.build_project()
    role = f.build_project_role(project=project, slug="member")

    invitation = f.build_project_invitation(
        user=None,
        project=project,
        role=role,
        email="test@email.com",
        invited_by=project.created_by,
    )

    with patch(
        "projects.invitations.services.ProjectInvitationToken", autospec=True
    ) as FakeProjectInvitationToken:
        FakeProjectInvitationToken.create_for_object.return_value = "invitation-token"

        await services.send_project_invitation_email(
            invitation=invitation,
            project=invitation.project,
            sender=invitation.invited_by,
        )

        assert len(tqmanager.pending_jobs) == 1

        job = tqmanager.pending_jobs[0]
        assert "send_email" in job["task_name"]

        args = job["args"]
        assert args["email_name"] == "project_invitation"
        assert args["to"] == invitation.email
        assert args["context"]["invitation_token"] == "invitation-token"
        assert args["context"]["project_color"] == invitation.project.color
        assert args["context"]["project_workspace"] == invitation.project.workspace.name
        assert args["context"]["project_image_url"] is None
        assert args["context"]["project_name"] == invitation.project.name
        assert args["context"]["project_id"] == invitation.project.b64id
        assert args["context"]["receiver_name"] is None
        assert args["context"]["sender_name"] == invitation.invited_by.full_name


#######################################################
# create_project_invitations
#######################################################


async def test_create_project_invitations_non_existing_role(tqmanager):
    project = f.build_project()
    role = f.build_project_role(project=project, slug="role")
    invitations = [{"email": "test@email.com", "role_id": NOT_EXISTING_UUID}]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
    ):
        fake_memberships_repositories.list_roles.return_value = [role]

        with pytest.raises(ex.NonExistingRoleError):
            await services.create_project_invitations(
                project=project, invitations=invitations, invited_by=project.created_by
            )

        assert len(tqmanager.pending_jobs) == 0
        fake_invitations_events.emit_event_when_project_invitations_are_created.assert_not_awaited()


async def test_create_project_invitations_already_member(tqmanager):
    user = f.build_user()
    project = f.build_project()
    role = f.build_project_role(project=project, slug="member")
    invitations = [{"email": user.email, "role_id": role.id}]

    with (
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_repositories", autospec=True
        ) as fake_invitations_repo,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
    ):
        fake_memberships_repositories.list_roles.return_value = [role]
        fake_memberships_repositories.list_members.return_value = [user]
        fake_users_services.list_users_emails_as_dict.return_value = {user.email: user}
        fake_users_services.list_users_usernames_as_dict.return_value = {}

        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=project.created_by
        )

        fake_invitations_repo.create_invitations.assert_not_awaited()
        assert len(tqmanager.pending_jobs) == 0
        fake_invitations_events.emit_event_when_project_invitations_are_created.assert_not_awaited()


async def test_create_project_invitations_with_pending_invitations(tqmanager):
    project = f.build_project()
    role = f.build_project_role(project=project, slug="owner", is_owner=True)
    role2 = f.build_project_role(project=project, slug="member")
    project.created_by.project_role = role
    created_at = aware_utcnow() - timedelta(days=1)  # to avoid time spam
    invitation = f.build_project_invitation(
        project=project,
        user=None,
        role=role,
        email="test@email.com",
        created_at=created_at,
        invited_by=project.created_by,
    )
    invitations = [{"email": invitation.email, "role_id": role2.id}]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
    ):
        fake_memberships_repositories.list_roles.return_value = [role2]
        fake_memberships_repositories.get_invitation.return_value = invitation
        fake_users_services.list_users_emails_as_dict.return_value = {}
        fake_users_services.list_users_usernames_as_dict.return_value = {}

        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=project.created_by
        )

        fake_memberships_repositories.bulk_update_invitations.assert_awaited_once()

        assert len(tqmanager.pending_jobs) == 1
        fake_invitations_events.emit_event_when_project_invitations_are_created.assert_awaited_once()


async def test_create_project_invitations_with_pending_invitations_time_spam(tqmanager):
    project = f.build_project()
    role = f.build_project_role(project=project, slug="owner", is_owner=True)
    role2 = f.build_project_role(project=project, slug="member")
    project.created_by.project_role = role
    invitation = f.build_project_invitation(
        user=None,
        project=project,
        role=role,
        email="test@email.com",
        invited_by=project.created_by,
    )
    invitations = [{"email": invitation.email, "role_id": role2.id}]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        override_settings(**{"INVITATION_RESEND_TIME": 10}),
    ):
        fake_memberships_repositories.list_roles.return_value = [role2]
        fake_memberships_repositories.get_invitation.return_value = invitation
        fake_users_services.list_users_emails_as_dict.return_value = {}
        fake_users_services.list_users_usernames_as_dict.return_value = {}

        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=project.created_by
        )

        fake_memberships_repositories.bulk_update_invitations.assert_awaited_once()

        assert len(tqmanager.pending_jobs) == 0
        fake_invitations_events.emit_event_when_project_invitations_are_created.assert_awaited_once()


async def test_create_project_invitations_with_accepted_invitations():
    project = f.build_project()
    role = f.build_project_role(project=project, slug="owner", is_owner=True)
    role2 = f.build_project_role(project=project, slug="member")
    project.created_by.project_role = role
    invitation = f.build_project_invitation(
        project=project,
        user=None,
        role=role,
        email="test@email.com",
        invited_by=project.created_by,
        status=InvitationStatus.ACCEPTED,
    )
    invitations = [{"email": invitation.email, "role_id": role2.id}]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
        pytest.raises(ex.InvitationAlreadyAcceptedError),
    ):
        fake_memberships_repositories.list_roles.return_value = [role2]
        fake_memberships_repositories.get_invitation.return_value = invitation
        fake_users_services.list_users_emails_as_dict.return_value = {}
        fake_users_services.list_users_usernames_as_dict.return_value = {}

        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=project.created_by
        )
        fake_memberships_repositories.bulk_update_invitations.assert_not_awaited()


async def test_create_project_invitations_with_revoked_invitations(tqmanager):
    project = f.build_project()
    role = f.build_project_role(project=project, slug="owner", is_owner=True)
    role2 = f.build_project_role(project=project, slug="member")
    project.created_by.project_role = role
    created_at = aware_utcnow() - timedelta(days=1)  # to avoid time spam
    invitation = f.build_project_invitation(
        project=project,
        user=None,
        role=role,
        email="test@email.com",
        created_at=created_at,
        invited_by=project.created_by,
        status=InvitationStatus.REVOKED,
    )
    invitations = [{"email": invitation.email, "role_id": role2.id}]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
    ):
        fake_memberships_repositories.list_roles.return_value = [role2]
        fake_memberships_repositories.get_invitation.return_value = invitation
        fake_users_services.list_users_emails_as_dict.return_value = {}
        fake_users_services.list_users_usernames_as_dict.return_value = {}

        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=project.created_by
        )

        fake_memberships_repositories.bulk_update_invitations.assert_awaited_once()

        assert len(tqmanager.pending_jobs) == 1
        fake_invitations_events.emit_event_when_project_invitations_are_created.assert_awaited_once()


async def test_create_project_invitations_with_revoked_invitations_time_spam(tqmanager):
    project = f.build_project()
    role = f.build_project_role(project=project, slug="owner", is_owner=True)
    role2 = f.build_project_role(project=project, slug="member")
    project.created_by.project_role = role
    invitation = f.build_project_invitation(
        project=project,
        user=None,
        role=role,
        email="test@email.com",
        invited_by=project.created_by,
        status=InvitationStatus.REVOKED,
    )
    invitations = [{"email": invitation.email, "role_id": role2.id}]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        override_settings(**{"INVITATION_RESEND_TIME": 10}),
    ):
        fake_memberships_repositories.list_roles.return_value = [role2]
        fake_memberships_repositories.get_invitation.return_value = invitation
        fake_users_services.list_users_emails_as_dict.return_value = {}
        fake_users_services.list_users_usernames_as_dict.return_value = {}

        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=project.created_by
        )

        fake_memberships_repositories.bulk_update_invitations.assert_awaited_once()

        assert len(tqmanager.pending_jobs) == 0
        fake_invitations_events.emit_event_when_project_invitations_are_created.assert_awaited_once()


async def test_create_project_invitations_by_emails(tqmanager):
    user1 = f.build_user()
    user2 = f.build_user(email="user-test@email.com")
    project = f.build_project()
    role1 = f.build_project_role(project=project, slug="owner", is_owner=True)
    role2 = f.build_project_role(project=project, slug="member")
    user1.project_role = role1

    invitations = [
        {"email": user2.email, "role_id": role1.id},
        {"email": "test@email.com", "role_id": role2.id},
    ]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
    ):
        fake_memberships_repositories.list_roles.return_value = [role1, role2]
        fake_users_services.list_users_emails_as_dict.return_value = {
            user2.email: user2
        }
        fake_users_services.list_users_usernames_as_dict.return_value = {}
        fake_memberships_repositories.get_invitation.side_effect = (
            ProjectInvitation.DoesNotExist
        )

        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=user1
        )

        fake_memberships_repositories.list_roles.assert_awaited_once_with(
            ProjectRole,
            filters={"project_id": project.id, "id__in": {role1.id, role2.id}},
        )
        fake_users_services.list_users_emails_as_dict.assert_awaited_once()
        fake_users_services.list_users_usernames_as_dict.assert_not_awaited()
        fake_memberships_repositories.create_invitations.assert_awaited_once()

        assert len(tqmanager.pending_jobs) == 2
        fake_invitations_events.emit_event_when_project_invitations_are_created.assert_awaited_once()


async def test_create_project_invitations_by_usernames(tqmanager):
    user1 = f.build_user()
    user2 = f.build_user()
    user3 = f.build_user()
    project = f.build_project()
    role1 = f.build_project_role(project=project, slug="owner", is_owner=True)
    role2 = f.build_project_role(project=project, slug="member")
    user1.project_role = role1

    invitations = [
        {"username": user2.username, "role_id": role1.id},
        {"username": user3.username, "role_id": role2.id},
    ]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
    ):
        fake_memberships_repositories.list_roles.return_value = [role1, role2]
        fake_users_services.list_users_emails_as_dict.return_value = {}
        fake_users_services.list_users_usernames_as_dict.return_value = {
            user2.username: user2,
            user3.username: user3,
        }
        fake_memberships_repositories.get_invitation.side_effect = (
            ProjectInvitation.DoesNotExist
        )

        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=user1
        )

        fake_memberships_repositories.list_roles.assert_awaited_once_with(
            ProjectRole,
            filters={"project_id": project.id, "id__in": {role1.id, role2.id}},
        )
        fake_memberships_repositories.create_invitations.assert_awaited_once()

        assert len(tqmanager.pending_jobs) == 2
        fake_invitations_events.emit_event_when_project_invitations_are_created.assert_awaited_once()


async def test_create_project_invitations_duplicated_email_username(tqmanager):
    user1 = f.build_user(email="test1@email.com", username="user1")
    user2 = f.build_user(email="test2@email.com", username="user2")
    user3 = f.build_user(email="test3@email.com", username="user3")
    user4 = f.build_user(email="test4@email.com", username="user4")
    project = f.build_project()
    role1 = f.build_project_role(project=project, slug="owner", is_owner=True)
    role2 = f.build_project_role(project=project, slug="member")
    user1.project_role = role1

    invitations = [
        {
            "username": user2.username,
            "email": "test2@email.com",
            "role_id": role2.id,
        },
        {"username": user3.username, "role_id": role2.id},
        {"username": user4.username, "role_id": role1.id},
        {"email": "test3@email.com", "role_id": role1.id},
        {"email": "test4@email.com", "role_id": role2.id},
    ]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
    ):
        fake_memberships_repositories.list_roles.return_value = [role1, role2]
        fake_users_services.list_users_emails_as_dict.return_value = {
            user3.email: user3,
            user4.email: user4,
        }
        fake_users_services.list_users_usernames_as_dict.return_value = {
            user2.username: user2,
            user3.username: user3,
            user4.username: user4,
        }
        fake_memberships_repositories.get_invitation.side_effect = (
            ProjectInvitation.DoesNotExist
        )

        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=user1
        )

        fake_memberships_repositories.list_roles.assert_awaited_once_with(
            ProjectRole,
            filters={"project_id": project.id, "id__in": {role1.id, role2.id}},
        )
        fake_users_services.list_users_emails_as_dict.assert_awaited_once()
        fake_users_services.list_users_usernames_as_dict.assert_awaited_once()
        fake_memberships_repositories.create_invitations.assert_awaited_once()

        assert len(tqmanager.pending_jobs) == 3
        assert list(map(lambda x: x["args"]["to"], tqmanager.pending_jobs)) == [
            user3.email,
            user4.email,
            user2.email,
        ]
        fake_invitations_events.emit_event_when_project_invitations_are_created.assert_awaited_once()


async def test_create_project_invitations_invalid_username(tqmanager):
    user1 = f.build_user(email="test@email.com", username="user1")
    project = f.build_project()
    role = f.build_project_role(project=project, slug="owner", is_owner=True)

    invitations = [{"username": "not existing username", "role_id": role.id}]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
        pytest.raises(ex.InvitationNonExistingUsernameError),
    ):
        fake_memberships_repositories.list_roles.return_value = [role]
        fake_users_services.list_users_emails_as_dict.return_value = {}
        fake_users_services.list_users_usernames_as_dict.return_value = {}

        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=user1
        )


async def test_create_project_invitations_owner_no_permission(tqmanager):
    user1 = f.build_user(email="test@email.com", username="user1")
    user2 = f.build_user(email="test@email.com", username="user2")
    user3 = f.build_user(email="test@email.com", username="user3")

    project = f.build_project()
    member_role = f.build_project_role(project=project, is_owner=False)
    owner_role = f.build_project_role(project=project, slug="owner", is_owner=True)
    existing_invitation = f.build_project_invitation(
        project=project, role=owner_role, user=user1
    )

    invitations = [
        {"email": user1.email, "role_id": member_role.id},
        {"username": user2.username, "role_id": owner_role.id},
    ]

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "memberships.services.users_services", autospec=True
        ) as fake_users_services,
    ):
        fake_memberships_repositories.list_roles.return_value = [
            member_role,
            owner_role,
        ]
        fake_users_services.list_users_emails_as_dict.return_value = {
            user2.username: user2,
        }
        fake_users_services.list_users_usernames_as_dict.return_value = {
            user1.email: user1,
        }
        fake_memberships_repositories.get_invitation.side_effect = (
            existing_invitation,
            ProjectInvitation.DoesNotExist,
            existing_invitation,
            ProjectInvitation.DoesNotExist,
        )

        user3.project_role = member_role
        with pytest.raises(ex.OwnerRoleNotAuthorisedError):
            await services.create_project_invitations(
                project=project, invitations=invitations, invited_by=user3
            )
        user3.project_role = owner_role
        await services.create_project_invitations(
            project=project, invitations=invitations, invited_by=user3
        )


#######################################################
# accept_project_invitation
#######################################################


async def test_accept_project_invitation_existing_workspace_membership() -> None:
    user = f.build_user()
    project = f.build_project()
    role = f.build_project_role(project=project)
    invitation = f.build_project_invitation(
        project=project, role=role, user=user, email=user.email
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.memberships_repositories", autospec=True
        ) as fake_pj_memberships_repo,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch(
            "projects.invitations.services.invitations_repositories", autospec=True
        ) as fake_invitations_repositories,
        patch(
            "projects.invitations.services.workspaces_invitations_services",
            autospec=True,
        ) as fake_workspaces_invitations_services,
        patch(
            "projects.invitations.services.workspaces_memberships_services",
            autospec=True,
        ) as fake_workspaces_memberships_services,
        patch_db_transaction(),
    ):
        fake_pj_memberships_repo.exists_membership.return_value = True
        fake_memberships_repositories.update_invitation.return_value = invitation
        await services.accept_project_invitation(invitation=invitation)

        fake_memberships_repositories.update_invitation.assert_awaited_once_with(
            invitation=invitation,
            values={"status": InvitationStatus.ACCEPTED},
        )
        fake_pj_memberships_repo.create_project_membership.assert_awaited_once_with(
            project=project, role=role, user=user
        )
        fake_invitations_events.emit_event_when_project_invitation_is_accepted.assert_awaited_once_with(
            invitation=invitation,
            membership=fake_pj_memberships_repo.create_project_membership.return_value,
            workspace_membership=None,
        )
        fake_pj_memberships_repo.exists_membership.assert_awaited_once_with(
            WorkspaceMembership,
            filters={
                "workspace_id": project.workspace_id,
                "user_id": invitation.user_id,
            },
        )
        fake_invitations_repositories.get_invitation.assert_not_awaited()
        fake_workspaces_invitations_services.accept_workspace_invitation.assert_not_awaited()
        fake_workspaces_memberships_services.create_default_workspace_membership.assert_not_awaited()


async def test_accept_project_invitation_existing_workspace_invitation() -> None:
    user = f.build_user()
    project = f.build_project()
    role = f.build_project_role(project=project)
    invitation = f.build_project_invitation(
        project=project, role=role, user=user, email=user.email
    )
    ws_role = f.build_workspace_role(workspace=project.workspace)
    ws_invitation = f.build_workspace_invitation(
        workspace=project.workspace, role=ws_role, user=user, email=user.email
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.memberships_repositories", autospec=True
        ) as fake_pj_memberships_repo,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch(
            "projects.invitations.services.invitations_repositories", autospec=True
        ) as fake_invitations_repositories,
        patch(
            "projects.invitations.services.workspaces_invitations_services",
            autospec=True,
        ) as fake_workspaces_invitations_services,
        patch(
            "projects.invitations.services.workspaces_memberships_services",
            autospec=True,
        ) as fake_workspaces_memberships_services,
        patch_db_transaction(),
    ):
        fake_pj_memberships_repo.exists_membership.return_value = False
        fake_memberships_repositories.update_invitation.return_value = invitation
        fake_invitations_repositories.get_invitation.return_value = ws_invitation
        await services.accept_project_invitation(invitation=invitation)

        fake_memberships_repositories.update_invitation.assert_awaited_once_with(
            invitation=invitation,
            values={"status": InvitationStatus.ACCEPTED},
        )
        fake_pj_memberships_repo.create_project_membership.assert_awaited_once_with(
            project=project, role=role, user=user
        )
        fake_invitations_events.emit_event_when_project_invitation_is_accepted.assert_awaited_once_with(
            invitation=invitation,
            membership=fake_pj_memberships_repo.create_project_membership.return_value,
            workspace_membership=None,
        )
        fake_pj_memberships_repo.exists_membership.assert_awaited_once_with(
            WorkspaceMembership,
            filters={
                "workspace_id": project.workspace_id,
                "user_id": invitation.user_id,
            },
        )
        fake_invitations_repositories.get_invitation.assert_awaited_once_with(
            WorkspaceInvitation,
            filters={
                "workspace_id": project.workspace_id,
                "user_id": user.id,
                "status": InvitationStatus.PENDING,
            },
            select_related=["user", "workspace", "role"],
        )
        fake_workspaces_invitations_services.accept_workspace_invitation.assert_awaited_once_with(
            ws_invitation
        )
        fake_workspaces_memberships_services.create_default_workspace_membership.assert_not_awaited()


async def test_accept_project_invitation_no_workspace_membership_nor_invitation() -> (
    None
):
    user = f.build_user()
    project = f.build_project()
    role = f.build_project_role(project=project)
    invitation = f.build_project_invitation(
        project=project, role=role, user=user, email=user.email
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.memberships_repositories", autospec=True
        ) as fake_pj_memberships_repo,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch(
            "projects.invitations.services.invitations_repositories", autospec=True
        ) as fake_invitations_repositories,
        patch(
            "projects.invitations.services.workspaces_invitations_services",
            autospec=True,
        ) as fake_workspaces_invitations_services,
        patch(
            "projects.invitations.services.workspaces_memberships_services",
            autospec=True,
        ) as fake_workspaces_memberships_services,
        patch_db_transaction(),
    ):
        fake_pj_memberships_repo.exists_membership.return_value = False
        fake_memberships_repositories.update_invitation.return_value = invitation
        fake_invitations_repositories.get_invitation.side_effect = (
            WorkspaceInvitation.DoesNotExist
        )
        await services.accept_project_invitation(invitation=invitation)

        fake_memberships_repositories.update_invitation.assert_awaited_once_with(
            invitation=invitation,
            values={"status": InvitationStatus.ACCEPTED},
        )
        fake_pj_memberships_repo.create_project_membership.assert_awaited_once_with(
            project=project, role=role, user=user
        )
        fake_invitations_events.emit_event_when_project_invitation_is_accepted.assert_awaited_once_with(
            invitation=invitation,
            membership=fake_pj_memberships_repo.create_project_membership.return_value,
            workspace_membership=fake_workspaces_memberships_services.create_default_workspace_membership.return_value,
        )
        fake_pj_memberships_repo.exists_membership.assert_awaited_once_with(
            WorkspaceMembership,
            filters={
                "workspace_id": project.workspace_id,
                "user_id": invitation.user_id,
            },
        )
        fake_invitations_repositories.get_invitation.assert_awaited_once_with(
            WorkspaceInvitation,
            filters={
                "workspace_id": project.workspace_id,
                "user_id": user.id,
                "status": InvitationStatus.PENDING,
            },
            select_related=["user", "workspace", "role"],
        )
        fake_workspaces_invitations_services.accept_workspace_invitation.assert_not_awaited()
        fake_workspaces_memberships_services.create_default_workspace_membership.assert_awaited_once_with(
            project.workspace_id, user
        )


async def test_accept_project_invitation_error_invitation_has_already_been_accepted() -> (
    None
):
    user = f.build_user()
    project = f.build_project()
    role = f.build_project_role(project=project)
    invitation = f.build_project_invitation(
        project=project,
        role=role,
        user=user,
        status=InvitationStatus.ACCEPTED,
        email=user.email,
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.memberships_repositories", autospec=True
        ) as fake_pj_roles_repo,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch_db_transaction(),
        pytest.raises(ex.InvitationAlreadyAcceptedError),
    ):
        await services.accept_project_invitation(invitation=invitation)

        fake_memberships_repositories.accept_invitation.assert_not_awaited()
        fake_pj_roles_repo.create_project_membership.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_accepted.assert_not_awaited()


async def test_accept_project_invitation_error_invitation_has_been_revoked() -> None:
    user = f.build_user()
    project = f.build_project()
    role = f.build_project_role(project=project)
    invitation = f.build_project_invitation(
        project=project,
        role=role,
        user=user,
        status=InvitationStatus.REVOKED,
        email=user.email,
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.memberships_repositories", autospec=True
        ) as fake_pj_roles_repo,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch_db_transaction(),
        pytest.raises(ex.InvitationRevokedError),
    ):
        await services.accept_project_invitation(invitation=invitation)

        fake_memberships_repositories.accept_invitation.assert_not_awaited()
        fake_pj_roles_repo.create_project_membership.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_accepted.assert_not_awaited()


async def test_accept_project_invitation_error_invitation_has_been_denied() -> None:
    user = f.build_user()
    project = f.build_project()
    role = f.build_project_role(project=project)
    invitation = f.build_project_invitation(
        project=project,
        role=role,
        user=user,
        status=InvitationStatus.DENIED,
        email=user.email,
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.memberships_repositories", autospec=True
        ) as fake_pj_roles_repo,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch_db_transaction(),
        pytest.raises(ex.InvitationDeniedError),
    ):
        await services.accept_project_invitation(invitation=invitation)

        fake_memberships_repositories.accept_invitation.assert_not_awaited()
        fake_pj_roles_repo.create_project_membership.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_accepted.assert_not_awaited()


#######################################################
# accept_project_invitation_from_token
#######################################################


async def test_accept_project_invitation_from_token_ok() -> None:
    user = f.build_user()
    invitation = f.build_project_invitation(user=user, email=user.email)
    token = str(await ProjectInvitationToken.create_for_object(invitation))

    with (
        patch(
            "projects.invitations.services.get_project_invitation_by_token",
            autospec=True,
        ) as fake_get_project_invitation,
        patch(
            "projects.invitations.services.accept_project_invitation",
            autospec=True,
        ) as fake_accept_project_invitation,
    ):
        fake_get_project_invitation.return_value = invitation

        await services.accept_project_invitation_from_token(token=token, user=user)

        fake_get_project_invitation.assert_awaited_once_with(
            token=token, select_related=["user", "project", "role"]
        )
        fake_accept_project_invitation.assert_awaited_once_with(invitation=invitation)


async def test_accept_project_invitation_from_token_error_no_invitation_found() -> None:
    user = f.build_user()

    with (
        patch(
            "projects.invitations.services.get_project_invitation_by_token",
            autospec=True,
        ) as fake_get_project_invitation,
        patch(
            "projects.invitations.services.accept_project_invitation",
            autospec=True,
        ) as fake_accept_project_invitation,
        pytest.raises(ex.InvitationDoesNotExistError),
    ):
        fake_get_project_invitation.side_effect = ProjectInvitation.DoesNotExist

        await services.accept_project_invitation_from_token(
            token="some_token", user=user
        )

        fake_get_project_invitation.assert_awaited_once_with(token="some_token")
        fake_accept_project_invitation.assert_not_awaited()


async def test_accept_project_invitation_from_token_error_invitation_is_for_other_user() -> (
    None
):
    user = f.build_user()
    other_user = f.build_user()
    invitation = f.build_project_invitation(user=other_user, email=other_user.email)
    token = str(await ProjectInvitationToken.create_for_object(invitation))

    with (
        patch(
            "projects.invitations.services.get_project_invitation_by_token",
            autospec=True,
        ) as fake_get_project_invitation,
        patch(
            "projects.invitations.services.accept_project_invitation",
            autospec=True,
        ) as fake_accept_project_invitation,
        pytest.raises(ex.InvitationIsNotForThisUserError),
    ):
        fake_get_project_invitation.return_value = invitation

        await services.accept_project_invitation_from_token(token=token, user=user)

        fake_get_project_invitation.assert_awaited_once_with(token=token)
        fake_accept_project_invitation.assert_not_awaited()


async def test_accept_project_invitation_from_token_error_already_accepted() -> None:
    user = f.build_user()
    invitation = f.build_project_invitation(
        user=user, email=user.email, status=InvitationStatus.ACCEPTED
    )
    token = str(await ProjectInvitationToken.create_for_object(invitation))

    with (
        patch(
            "projects.invitations.services.get_project_invitation_by_token",
            autospec=True,
        ) as fake_get_project_invitation,
        patch("projects.invitations.services._sync_related_workspace_membership"),
        patch_db_transaction(),
        pytest.raises(ex.InvitationAlreadyAcceptedError),
    ):
        fake_get_project_invitation.return_value = invitation

        await services.accept_project_invitation_from_token(token=token, user=user)

        fake_get_project_invitation.assert_awaited_once_with(token=token)


async def test_accept_project_invitation_from_token_error_revoked() -> None:
    user = f.build_user()
    invitation = f.build_project_invitation(
        user=user, email=user.email, status=InvitationStatus.REVOKED
    )
    token = str(await ProjectInvitationToken.create_for_object(invitation))

    with (
        patch(
            "projects.invitations.services.get_project_invitation_by_token",
            autospec=True,
        ) as fake_get_project_invitation,
        patch("projects.invitations.services._sync_related_workspace_membership"),
        patch_db_transaction(),
        pytest.raises(ex.InvitationRevokedError),
    ):
        fake_get_project_invitation.return_value = invitation

        await services.accept_project_invitation_from_token(token=token, user=user)

        fake_get_project_invitation.assert_awaited_once_with(token=token)


async def test_accept_project_invitation_from_token_error_denied() -> None:
    user = f.build_user()
    invitation = f.build_project_invitation(
        user=user, email=user.email, status=InvitationStatus.DENIED
    )
    token = str(await ProjectInvitationToken.create_for_object(invitation))

    with (
        patch(
            "projects.invitations.services.get_project_invitation_by_token",
            autospec=True,
        ) as fake_get_project_invitation,
        patch("projects.invitations.services._sync_related_workspace_membership"),
        patch_db_transaction(),
        pytest.raises(ex.InvitationDeniedError),
    ):
        fake_get_project_invitation.return_value = invitation

        await services.accept_project_invitation_from_token(token=token, user=user)

        fake_get_project_invitation.assert_awaited_once_with(token=token)


#######################################################
# is_invitation_for_this_user
#######################################################


def test_is_invitation_for_this_user_ok_same_user() -> None:
    user = f.build_user()
    invitation = f.build_project_invitation(email=user.email, user=user)

    assert services.is_invitation_for_this_user(invitation=invitation, user=user)


def test_is_invitation_for_this_user_ok_same_email() -> None:
    user = f.build_user()
    invitation = f.build_project_invitation(email=user.email, user=None)

    assert services.is_invitation_for_this_user(invitation=invitation, user=user)


def test_is_invitation_for_this_user_error_different_user() -> None:
    user = f.build_user()
    other_user = f.build_user()
    invitation = f.build_project_invitation(user=other_user)

    assert not services.is_invitation_for_this_user(invitation=invitation, user=user)


def test_is_invitation_for_this_user_ok_different_email() -> None:
    user = f.build_user()
    other_user = f.build_user()
    invitation = f.build_project_invitation(email=other_user.email, user=None)

    assert not services.is_invitation_for_this_user(invitation=invitation, user=user)


#######################################################
# update_user_projects_invitations
#######################################################


async def test_update_user_projects_invitations() -> None:
    user = f.build_user()
    with (
        patch(
            "projects.invitations.services.invitations_repositories", autospec=True
        ) as fake_invitations_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch_db_transaction(),
    ):
        await services.update_user_projects_invitations(user=user)
        fake_invitations_repositories.update_user_invitations.assert_awaited_once_with(
            ProjectInvitation, user=user
        )
        fake_invitations_repositories.list_invitations.assert_awaited_once_with(
            ProjectInvitation,
            filters={"user": user, "status": InvitationStatus.PENDING},
            select_related=["user", "role", "project"],
        )
        fake_invitations_events.emit_event_when_project_invitations_are_updated.assert_awaited_once()


#######################################################
# resend_project_invitation
#######################################################


async def test_resend_project_invitation_by_username_ok() -> None:
    project = f.build_project()
    user = f.build_user()
    created_at = aware_utcnow() - timedelta(days=1)  # to avoid time spam
    invitation = f.build_project_invitation(
        project=project, user=user, email=user.email, created_at=created_at
    )
    now = aware_utcnow()

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.send_project_invitation_email", autospec=True
        ) as fake_send_project_invitation_email,
        patch("memberships.services.aware_utcnow") as fake_aware_utcnow,
    ):
        fake_aware_utcnow.return_value = now
        fake_send_project_invitation_email.return_value = None
        fake_memberships_repositories.update_invitation.return_value = invitation
        await services.resend_project_invitation(
            invitation=invitation, resent_by=project.created_by
        )
        fake_memberships_repositories.update_invitation.assert_awaited_once_with(
            invitation=invitation,
            values={
                "num_emails_sent": 2,
                "resent_at": now,
                "resent_by": project.created_by,
            },
        )
        fake_send_project_invitation_email.assert_awaited_once_with(
            invitation=invitation, project=project, sender=project.created_by
        )


async def test_resend_project_invitation_by_user_email_ok() -> None:
    project = f.build_project()
    user = f.build_user()
    created_at = aware_utcnow() - timedelta(days=1)  # to avoid time spam
    invitation = f.build_project_invitation(
        project=project, user=user, email=user.email, created_at=created_at
    )
    now = aware_utcnow()

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.send_project_invitation_email", autospec=True
        ) as fake_send_project_invitation_email,
        patch("memberships.services.aware_utcnow") as fake_aware_utcnow,
    ):
        fake_aware_utcnow.return_value = now
        fake_send_project_invitation_email.return_value = None
        fake_memberships_repositories.update_invitation.return_value = invitation
        await services.resend_project_invitation(
            invitation=invitation, resent_by=project.created_by
        )
        fake_memberships_repositories.update_invitation.assert_awaited_once_with(
            invitation=invitation,
            values={
                "num_emails_sent": 2,
                "resent_at": now,
                "resent_by": project.created_by,
            },
        )
        fake_send_project_invitation_email.assert_awaited_once_with(
            invitation=invitation, project=project, sender=project.created_by
        )


async def test_resend_project_invitation_by_email_ok() -> None:
    project = f.build_project()
    email = "user-test@email.com"
    created_at = aware_utcnow() - timedelta(days=1)  # to avoid time spam
    invitation = f.build_project_invitation(
        project=project, user=None, email=email, created_at=created_at
    )
    now = aware_utcnow()

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.send_project_invitation_email", autospec=True
        ) as fake_send_project_invitation_email,
        patch("memberships.services.aware_utcnow") as fake_aware_utcnow,
    ):
        fake_aware_utcnow.return_value = now
        fake_send_project_invitation_email.return_value = None
        fake_memberships_repositories.update_invitation.return_value = invitation
        await services.resend_project_invitation(
            invitation=invitation, resent_by=project.created_by
        )
        fake_memberships_repositories.update_invitation.assert_awaited_once_with(
            invitation=invitation,
            values={
                "num_emails_sent": 2,
                "resent_at": now,
                "resent_by": project.created_by,
            },
        )
        fake_send_project_invitation_email.assert_awaited_once_with(
            invitation=invitation, project=project, sender=project.created_by
        )


async def test_resend_project_invitation_already_accepted() -> None:
    project = f.build_project()
    email = "user-test@email.com"
    invitation = f.build_project_invitation(
        project=project, user=None, email=email, status=InvitationStatus.ACCEPTED
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.send_project_invitation_email", autospec=True
        ) as fake_send_project_invitation_email,
        pytest.raises(ex.InvitationAlreadyAcceptedError),
    ):
        fake_send_project_invitation_email.return_value = None
        await services.resend_project_invitation(
            invitation=invitation, resent_by=project.created_by
        )
        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_send_project_invitation_email.assert_not_awaited()


async def test_resend_project_invitation_revoked() -> None:
    project = f.build_project()
    email = "user-test@email.com"
    invitation = f.build_project_invitation(
        project=project, user=None, email=email, status=InvitationStatus.REVOKED
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.send_project_invitation_email", autospec=True
        ) as fake_send_project_invitation_email,
        pytest.raises(ex.InvitationRevokedError),
    ):
        fake_send_project_invitation_email.return_value = None
        await services.resend_project_invitation(
            invitation=invitation, resent_by=project.created_by
        )
        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_send_project_invitation_email.assert_not_awaited()


async def test_resend_project_invitation_num_emails_sent_in_limit() -> None:
    project = f.build_project()
    email = "user-test@email.com"
    invitation = f.build_project_invitation(
        project=project, user=None, email=email, num_emails_sent=10
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.send_project_invitation_email", autospec=True
        ) as fake_send_project_invitation_email,
        override_settings(**{"INVITATION_RESEND_LIMIT": 10}),
    ):
        await services.resend_project_invitation(
            invitation=invitation, resent_by=project.created_by
        )
        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_send_project_invitation_email.assert_not_awaited()


async def test_resend_project_invitation_resent_at_in_limit() -> None:
    project = f.build_project()
    email = "user-test@email.com"
    invitation = f.build_project_invitation(
        project=project, user=None, email=email, resent_at=aware_utcnow()
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.send_project_invitation_email", autospec=True
        ) as fake_send_project_invitation_email,
        override_settings(**{"INVITATION_RESEND_TIME": 10}),
    ):
        await services.resend_project_invitation(
            invitation=invitation, resent_by=project.created_by
        )
        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_send_project_invitation_email.assert_not_awaited()


async def test_resend_project_invitation_resent_after_create() -> None:
    project = f.build_project()
    email = "user-test@email.com"
    invitation = f.build_project_invitation(project=project, user=None, email=email)

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.send_project_invitation_email", autospec=True
        ) as fake_send_project_invitation_email,
        override_settings(**{"INVITATION_RESEND_TIME": 10}),
    ):
        await services.resend_project_invitation(
            invitation=invitation, resent_by=project.created_by
        )
        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_send_project_invitation_email.assert_not_awaited()


#######################################################
# revoke_project_invitation
#######################################################


async def test_revoke_project_invitation_ok() -> None:
    project = f.build_project()
    user = f.build_user()
    invitation = f.build_project_invitation(
        project=project, user=user, email=user.email
    )
    now = aware_utcnow()

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch("memberships.services.aware_utcnow") as fake_aware_utcnow,
    ):
        fake_aware_utcnow.return_value = now
        fake_memberships_repositories.update_invitation.return_value = invitation
        await services.revoke_project_invitation(
            invitation=invitation, revoked_by=project.created_by
        )
        fake_memberships_repositories.update_invitation.assert_awaited_once_with(
            invitation=invitation,
            values={
                "status": InvitationStatus.REVOKED,
                "revoked_at": now,
                "revoked_by": project.created_by,
            },
        )
        fake_invitations_events.emit_event_when_project_invitation_is_revoked.assert_awaited_once_with(
            invitation=invitation
        )


async def test_revoke_project_invitation_already_accepted() -> None:
    user = f.build_user()
    project = f.build_project()
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        status=InvitationStatus.ACCEPTED,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        pytest.raises(ex.InvitationAlreadyAcceptedError),
    ):
        await services.revoke_project_invitation(
            invitation=invitation, revoked_by=project.created_by
        )

        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_revoked.assert_not_awaited()


async def test_revoke_project_invitation_revoked() -> None:
    user = f.build_user()
    project = f.build_project()
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        status=InvitationStatus.REVOKED,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        pytest.raises(ex.InvitationRevokedError),
    ):
        await services.revoke_project_invitation(
            invitation=invitation, revoked_by=project.created_by
        )

        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_revoked.assert_not_awaited()


async def test_revoke_project_invitation_denied() -> None:
    user = f.build_user()
    project = f.build_project()
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        status=InvitationStatus.DENIED,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        pytest.raises(ex.InvitationDeniedError),
    ):
        await services.revoke_project_invitation(
            invitation=invitation, revoked_by=project.created_by
        )

        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_revoked.assert_not_awaited()


#######################################################
# deny_project_invitation
#######################################################


async def test_deny_project_invitation_ok() -> None:
    project = f.build_project()
    user = f.build_user()
    invitation = f.build_project_invitation(
        project=project, user=user, email=user.email
    )

    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
    ):
        fake_memberships_repositories.update_invitation.return_value = invitation
        await services.deny_project_invitation(
            invitation=invitation,
        )
        fake_memberships_repositories.update_invitation.assert_awaited_once_with(
            invitation=invitation,
            values={
                "status": InvitationStatus.DENIED,
            },
        )
        fake_invitations_events.emit_event_when_project_invitation_is_denied.assert_awaited_once_with(
            invitation=invitation
        )


async def test_deny_project_invitation_already_accepted() -> None:
    user = f.build_user()
    project = f.build_project()
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        status=InvitationStatus.ACCEPTED,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        pytest.raises(ex.InvitationAlreadyAcceptedError),
    ):
        await services.deny_project_invitation(invitation=invitation)

        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_denied.assert_not_awaited()


async def test_deny_project_invitation_revoked() -> None:
    user = f.build_user()
    project = f.build_project()
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        status=InvitationStatus.REVOKED,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        pytest.raises(ex.InvitationRevokedError),
    ):
        await services.deny_project_invitation(invitation=invitation)

        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_denied.assert_not_awaited()


async def test_deny_project_invitation_denied() -> None:
    user = f.build_user()
    project = f.build_project()
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        status=InvitationStatus.DENIED,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        pytest.raises(ex.InvitationDeniedError),
    ):
        await services.deny_project_invitation(invitation=invitation)

        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_denied.assert_not_awaited()


async def test_deny_project_invitation_no_user() -> None:
    project = f.build_project()
    invitation = f.build_project_invitation(
        project=project,
        email="test@email.com",
        status=InvitationStatus.PENDING,
        user=None,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        pytest.raises(ex.InvitationHasNoUserYetError),
    ):
        await services.deny_project_invitation(invitation=invitation)

        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_denied.assert_not_awaited()


#######################################################
# update_project_invitation
#######################################################


async def test_update_project_invitation_role_invitation_accepted() -> None:
    user = f.build_user()
    project = f.build_project()
    member_role = f.build_project_role(project=project, is_owner=False)
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        status=InvitationStatus.ACCEPTED,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        pytest.raises(ex.InvitationAlreadyAcceptedError),
    ):
        await services.update_project_invitation(
            invitation=invitation, role_id=member_role.id, user=f.build_user()
        )

        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_updated.assert_not_awaited()


async def test_update_project_invitation_role_invitation_revoked() -> None:
    user = f.build_user()
    project = f.build_project()
    member_role = f.build_project_role(project=project, is_owner=False)
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        status=InvitationStatus.REVOKED,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        pytest.raises(ex.InvitationRevokedError),
    ):
        await services.update_project_invitation(
            invitation=invitation, role_id=member_role.id, user=f.build_user()
        )

        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_updated.assert_not_awaited()


async def test_update_project_invitation_role_invitation_denied() -> None:
    user = f.build_user()
    project = f.build_project()
    member_role = f.build_project_role(project=project, is_owner=False)
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        status=InvitationStatus.DENIED,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        pytest.raises(ex.InvitationDeniedError),
    ):
        await services.update_project_invitation(
            invitation=invitation, role_id=member_role.id, user=f.build_user()
        )

        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_updated.assert_not_awaited()


async def test_update_project_invitation_role_non_existing_role():
    project = f.build_project()
    user = f.build_user()
    member_role = f.build_project_role(project=project, is_owner=False)
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch_db_transaction(),
        pytest.raises(ex.NonExistingRoleError),
    ):
        fake_memberships_repositories.get_role.side_effect = ProjectRole.DoesNotExist

        await services.update_project_invitation(
            invitation=invitation, role_id=NOT_EXISTING_UUID, user=f.build_user()
        )
        fake_memberships_repositories.get_role.assert_awaited_once_with(
            ProjectRole,
            filters={"project_id": project.id, "id": NOT_EXISTING_UUID},
        )
        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_updated.assert_not_awaited()


async def test_update_project_invitation_role_ok():
    project = f.build_project()
    user = f.build_user()
    member_role = f.build_project_role(project=project, is_owner=False)
    member_role2 = f.build_project_role(project=project, is_owner=False)
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch_db_transaction(),
    ):
        fake_memberships_repositories.get_role.return_value = member_role2
        updated_invitation = await services.update_project_invitation(
            invitation=invitation, role_id=member_role2.id, user=f.build_user()
        )
        fake_memberships_repositories.get_role.assert_awaited_once_with(
            ProjectRole, filters={"project_id": project.id, "id": member_role2.id}
        )
        fake_memberships_repositories.update_invitation.assert_awaited_once_with(
            invitation=invitation, values={"role": member_role2}
        )
        fake_invitations_events.emit_event_when_project_invitation_is_updated.assert_awaited_once_with(
            invitation=updated_invitation
        )


async def test_update_project_invitation_role_owner():
    project = f.build_project()
    user = f.build_user()
    member_role = f.build_project_role(project=project, is_owner=False)
    member_role2 = f.build_project_role(project=project, is_owner=False)
    owner_role = f.build_project_role(project=project, is_owner=True)
    invitation = f.build_project_invitation(
        project=project,
        user=user,
        email=user.email,
        role=member_role,
        status=InvitationStatus.PENDING,
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.invitations.services.invitations_events", autospec=True
        ) as fake_invitations_events,
        patch_db_transaction(),
    ):
        fake_memberships_repositories.get_role.return_value = owner_role
        with pytest.raises(ex.OwnerRoleNotAuthorisedError):
            await services.update_project_invitation(
                invitation=invitation, role_id=owner_role.id, user=f.build_user()
            )
        fake_memberships_repositories.get_role.assert_awaited_once_with(
            ProjectRole, filters={"project_id": project.id, "id": owner_role.id}
        )
        fake_memberships_repositories.update_invitation.assert_not_awaited()
        fake_invitations_events.emit_event_when_project_invitation_is_updated.assert_not_awaited()
        owner_user = f.build_user()
        owner_user.project_role = owner_role
        updated_invitation = await services.update_project_invitation(
            invitation=invitation, role_id=owner_role.id, user=owner_user
        )
        fake_memberships_repositories.update_invitation.assert_awaited_once_with(
            invitation=invitation, values={"role": owner_role}
        )
        fake_invitations_events.emit_event_when_project_invitation_is_updated.assert_awaited_once_with(
            invitation=updated_invitation
        )


#######################################################
# misc has_pending_project_invitation
#######################################################


async def test_has_pending_project_invitation() -> None:
    user = f.build_user()
    project = f.build_project()

    with patch(
        "memberships.services.memberships_repositories", autospec=True
    ) as fake_pj_memberships_repositories:
        invitation = f.build_project_invitation(
            email=user.email, user=user, project=project
        )
        fake_pj_memberships_repositories.exists_invitation.return_value = True
        res = await services.has_pending_invitation(reference_object=project, user=user)
        assert res is True

        fake_pj_memberships_repositories.exists_invitation.return_value = False
        res = await services.has_pending_invitation(reference_object=project, user=user)
        assert res is False

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

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.conf import settings

from memberships.choices import InvitationStatus
from memberships.services.exceptions import (
    BadInvitationTokenError,
    MembershipIsTheOnlyOwnerError,
)
from ninja_jwt.exceptions import TokenError
from ninja_jwt.schema import TokenObtainPairOutputSchema
from projects.invitations.models import ProjectInvitation
from projects.memberships.models import ProjectMembership
from projects.projects.models import Project
from tests.utils import factories as f
from tests.utils.utils import patch_db_transaction, preserve_real_attrs
from users import services
from users.models import User
from users.services import exceptions as ex
from users.tokens import ResetPasswordToken, VerifyUserToken
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships.models import WorkspaceMembership
from workspaces.workspaces.models import Workspace

##########################################################
# create_user
##########################################################


@pytest.mark.parametrize(
    "project_invitation_token, workspace_invitation_token, accept_project_invitation, accept_workspace_invitation",
    [
        ("eyJ0Token", True, None, None),
        (None, None, "eyJ0Token", True),
    ],
)
async def test_create_user_ok_accept_invitation(
    project_invitation_token,
    accept_project_invitation,
    workspace_invitation_token,
    accept_workspace_invitation,
    tqmanager,
):
    email = "email@email.com"
    username = "email"
    full_name = "Full Name"
    color = 8
    password = "CorrectP4ssword$"
    lang = "es-ES"
    user = f.build_user(
        id=1,
        email=email,
        username=username,
        full_name=full_name,
        color=color,
        lang=lang,
    )

    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch(
            "users.services._generate_verify_user_token", return_value="verify_token"
        ) as fake_user_token,
        patch("users.services.aware_utcnow", autospec=True) as fake_aware_utcnow,
    ):
        fake_users_repo.get_user.side_effect = User.DoesNotExist
        fake_users_repo.create_user.return_value = user

        await services.create_user(
            email=email,
            full_name=full_name,
            color=color,
            password=password,
            accept_project_invitation=accept_project_invitation,
            project_invitation_token=project_invitation_token,
            accept_workspace_invitation=accept_workspace_invitation,
            workspace_invitation_token=workspace_invitation_token,
            lang=lang,
            accepted_terms=True,
        )

        fake_users_repo.create_user.assert_awaited_once_with(
            email=email,
            full_name=full_name,
            color=color,
            password=password,
            lang=lang,
            acceptance_date=fake_aware_utcnow.return_value,
        )
        assert len(tqmanager.pending_jobs) == 1
        job = tqmanager.pending_jobs[0]
        assert "send_email" in job["task_name"]
        assert job["args"] == {
            "email_name": "sign_up",
            "to": "email@email.com",
            "lang": "es-ES",
            "context": {"verification_token": "verify_token"},
        }

        fake_user_token.assert_awaited_once_with(
            user=user,
            project_invitation_token=project_invitation_token,
            accept_project_invitation=accept_project_invitation,
            workspace_invitation_token=workspace_invitation_token,
            accept_workspace_invitation=accept_workspace_invitation,
        )


async def test_create_user_default_instance_lang(tqmanager):
    email = "email@email.com"
    username = "email"
    full_name = "Full Name"
    password = "CorrectP4ssword$"
    lang = None
    color = 1
    default_instance_lang = settings.LANGUAGE_CODE
    user = f.build_user(
        id=1,
        email=email,
        username=username,
        full_name=full_name,
        lang=default_instance_lang,
        color=color,
    )

    accept_project_invitation = True
    project_invitation_token = "eyJ0Token"

    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch(
            "users.services._generate_verify_user_token", return_value="verify_token"
        ) as fake_user_token,
        patch("users.services.aware_utcnow", autospec=True) as fake_aware_utcnow,
    ):
        fake_users_repo.get_user.side_effect = User.DoesNotExist
        fake_users_repo.create_user.return_value = user

        await services.create_user(
            email=email,
            full_name=full_name,
            password=password,
            accept_project_invitation=accept_project_invitation,
            project_invitation_token=project_invitation_token,
            lang=lang,
            color=color,
            accepted_terms=True,
        )

        fake_users_repo.create_user.assert_awaited_once_with(
            email=email,
            full_name=full_name,
            color=color,
            password=password,
            lang=default_instance_lang,
            acceptance_date=fake_aware_utcnow.return_value,
        )
        assert len(tqmanager.pending_jobs) == 1
        job = tqmanager.pending_jobs[0]
        assert "send_email" in job["task_name"]
        assert job["args"] == {
            "email_name": "sign_up",
            "to": "email@email.com",
            "lang": default_instance_lang,
            "context": {"verification_token": "verify_token"},
        }

        fake_user_token.assert_awaited_once_with(
            user=user,
            project_invitation_token=project_invitation_token,
            accept_project_invitation=accept_project_invitation,
            workspace_invitation_token=None,
            accept_workspace_invitation=True,
        )


async def test_create_user_unverified(tqmanager):
    email = "email@email.com"
    username = "email"
    full_name = "Full Name"
    color = 7
    user = f.build_user(
        id=1,
        email=email,
        username=username,
        full_name=full_name,
        is_active=False,
        color=color,
    )

    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch(
            "users.services._generate_verify_user_token", return_value="verify_token"
        ),
    ):
        fake_users_repo.get_user.return_value = user
        fake_users_repo.update_user.return_value = user
        await services.create_user(
            email=email,
            full_name="New Full Name",
            password="NewCorrectP4ssword&",
            accepted_terms=True,
        )

        fake_users_repo.update_user.assert_awaited_once()
        assert len(tqmanager.pending_jobs) == 1
        job = tqmanager.pending_jobs[0]
        assert "send_email" in job["task_name"]
        assert job["args"] == {
            "email_name": "sign_up",
            "to": "email@email.com",
            "lang": "en-US",
            "context": {"verification_token": "verify_token"},
        }


async def test_create_user_email_exists():
    with (
        pytest.raises(ex.EmailAlreadyExistsError),
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
    ):
        fake_users_repo.get_user.return_value = MagicMock(is_active=True)
        await services.create_user(
            email="dup.email@email.com",
            full_name="Full Name",
            password="CorrectP4ssword&",
            accepted_terms=True,
        )


async def test_create_user_not_accepted_terms():
    with (
        patch(
            "users.services.users_repositories.get_user",
            autospec=True,
            side_effect=User.DoesNotExist,
        ),
        pytest.raises(ValueError),
    ):
        await services.create_user(
            email="dup.email@email.com",
            full_name="Full Name",
            password="CorrectP4ssword&",
            accepted_terms=False,
        )


##########################################################
# verify_user
##########################################################


async def test_verify_user():
    user = f.build_user(is_active=False)
    now = datetime.now(timezone.utc)

    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch(
            "users.services.project_invitations_services", autospec=True
        ) as fake_project_invitations_services,
        patch(
            "users.services.workspace_invitations_services", autospec=True
        ) as fake_workspace_invitations_services,
        patch("users.services.aware_utcnow") as fake_aware_utcnow,
        patch_db_transaction(),
    ):
        fake_aware_utcnow.return_value = now
        await services._verify_user(user=user)
        fake_users_repo.update_user.assert_awaited_with(
            user=user,
            values={"is_active": True, "date_verification": now},
        )
        fake_project_invitations_services.update_user_projects_invitations.assert_awaited_once_with(
            user=user,
        )
        fake_workspace_invitations_services.update_user_workspaces_invitations.assert_awaited_once_with(
            user=user,
        )


##########################################################
# verify_user_from_token
##########################################################


async def test_verify_user_ok_no_invitation_tokens_to_accept():
    user = f.build_user(is_active=False)
    token_data = {"user_id": 1}
    auth_credentials = TokenObtainPairOutputSchema(
        access="token", refresh="refresh", username=user.username
    )

    with (
        patch("users.services.VerifyUserToken", autospec=True) as FakeVerifyUserToken,
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch("users.services.auth_services", autospec=True) as fake_auth_services,
        patch(
            "users.services.project_invitations_services", autospec=True
        ) as fake_pj_invitations_services,
        patch(
            "users.services.workspace_invitations_services", autospec=True
        ) as fake_ws_invitations_services,
        patch_db_transaction(),
    ):
        FakeVerifyUserToken.return_value.payload = token_data
        preserve_real_attrs(FakeVerifyUserToken.return_value, VerifyUserToken, ["get"])
        preserve_real_attrs(
            FakeVerifyUserToken.return_value.blacklist,
            VerifyUserToken.blacklist,
            ["__code__"],
        )
        fake_auth_services.create_auth_credentials.return_value = auth_credentials
        fake_users_repo.get_user.return_value = user

        info = await services.verify_user_from_token("some_token")

        assert info.auth == auth_credentials
        assert info.project_invitation is None

        FakeVerifyUserToken.return_value.blacklist.assert_called_once()
        fake_users_repo.get_user.assert_awaited_once_with(
            filters={"id": token_data["user_id"]}
        )

        fake_pj_invitations_services.update_user_projects_invitations.assert_awaited_once_with(
            user=user
        )
        fake_ws_invitations_services.update_user_workspaces_invitations.assert_awaited_once_with(
            user=user
        )

        fake_pj_invitations_services.accept_project_invitation_from_token.assert_not_awaited()
        fake_ws_invitations_services.accept_workspace_invitation_from_token.assert_not_awaited()
        fake_pj_invitations_services.get_project_invitation_by_token.assert_not_awaited()
        fake_ws_invitations_services.get_workspace_invitation.assert_not_awaited()

        fake_auth_services.create_auth_credentials.assert_awaited_once_with(user=user)

        fake_users_repo.update_user.assert_awaited_once()


@pytest.mark.parametrize(
    "accept_project_invitation",
    [True, False],
)
async def test_verify_user_ok_accepting_or_not_a_project_invitation_token(
    accept_project_invitation,
):
    user = f.build_user(is_active=False)
    project_invitation = f.build_project_invitation()
    project_invitation_token = "invitation_token"
    auth_credentials = TokenObtainPairOutputSchema(
        access="token", refresh="refresh", username=user.username
    )

    with (
        patch("users.services.VerifyUserToken", autospec=True) as FakeVerifyUserToken,
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch("users.services.auth_services", autospec=True) as fake_auth_services,
        patch(
            "users.services.project_invitations_services", autospec=True
        ) as fake_pj_invitations_services,
        patch(
            "users.services.workspace_invitations_services", autospec=True
        ) as fake_ws_invitations_services,
        patch_db_transaction(),
    ):
        FakeVerifyUserToken.return_value.get.side_effect = [
            1,
            None,
            project_invitation_token,
            accept_project_invitation,
        ]
        preserve_real_attrs(
            FakeVerifyUserToken.return_value.blacklist,
            VerifyUserToken.blacklist,
            ["__code__"],
        )
        fake_auth_services.create_auth_credentials.return_value = auth_credentials
        fake_pj_invitations_services.get_project_invitation_by_token.return_value = (
            project_invitation
        )
        fake_users_repo.get_user.return_value = user

        info = await services.verify_user_from_token("some_token")

        assert info.auth == auth_credentials
        assert info.project_invitation.project.name == project_invitation.project.name

        FakeVerifyUserToken.return_value.blacklist.assert_called_once()
        fake_users_repo.get_user.assert_awaited_once_with(filters={"id": 1})
        fake_pj_invitations_services.update_user_projects_invitations.assert_awaited_once_with(
            user=user
        )
        fake_ws_invitations_services.update_user_workspaces_invitations.assert_awaited_once_with(
            user=user
        )

        FakeVerifyUserToken.return_value.get.assert_any_call(
            "workspace_invitation_token", None
        )
        FakeVerifyUserToken.return_value.get.assert_any_call(
            "project_invitation_token", None
        )
        FakeVerifyUserToken.return_value.get.assert_any_call(
            "accept_project_invitation", False
        )
        fake_pj_invitations_services.get_project_invitation_by_token.assert_awaited_once_with(
            token=project_invitation_token
        )
        if accept_project_invitation:
            fake_pj_invitations_services.accept_project_invitation_from_token.assert_awaited_once_with(
                token=project_invitation_token, user=user
            )
        else:
            fake_pj_invitations_services.accept_project_invitation_from_token.assert_not_awaited()

        fake_auth_services.create_auth_credentials.assert_awaited_once_with(user=user)


@pytest.mark.parametrize(
    "accept_workspace_invitation",
    [True, False],
)
async def test_verify_user_ok_accepting_or_not_a_workspace_invitation_token(
    accept_workspace_invitation,
):
    user = f.build_user(is_active=False)
    workspace_invitation = f.build_workspace_invitation()
    workspace_invitation_token = "invitation_token"
    auth_credentials = TokenObtainPairOutputSchema(
        access="token", refresh="refresh", username=user.username
    )

    with (
        patch("users.services.VerifyUserToken", autospec=True) as FakeVerifyUserToken,
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch("users.services.auth_services", autospec=True) as fake_auth_services,
        patch(
            "users.services.project_invitations_services", autospec=True
        ) as fake_pj_invitations_services,
        patch(
            "users.services.workspace_invitations_services", autospec=True
        ) as fake_ws_invitations_services,
        patch_db_transaction(),
    ):
        # Second call will be `verify_token.get("project_invitation_token", None)` and should return None
        FakeVerifyUserToken.return_value.get.side_effect = [
            1,
            workspace_invitation_token,
            accept_workspace_invitation,
        ]
        preserve_real_attrs(
            FakeVerifyUserToken.return_value.blacklist,
            VerifyUserToken.blacklist,
            ["__code__"],
        )
        fake_auth_services.create_auth_credentials.return_value = auth_credentials
        fake_ws_invitations_services.get_workspace_invitation_by_token.return_value = (
            workspace_invitation
        )
        fake_users_repo.get_user.return_value = user

        info = await services.verify_user_from_token("some_token")

        assert info.auth == auth_credentials
        assert (
            info.workspace_invitation.workspace.name
            == workspace_invitation.workspace.name
        )

        FakeVerifyUserToken.return_value.blacklist.assert_called_once()
        fake_users_repo.get_user.assert_awaited_once_with(filters={"id": 1})
        fake_pj_invitations_services.update_user_projects_invitations.assert_awaited_once_with(
            user=user
        )
        fake_ws_invitations_services.update_user_workspaces_invitations.assert_awaited_once_with(
            user=user
        )

        FakeVerifyUserToken.return_value.get.assert_any_call(
            "workspace_invitation_token", None
        )
        FakeVerifyUserToken.return_value.get.assert_any_call(
            "accept_workspace_invitation", False
        )
        fake_ws_invitations_services.get_workspace_invitation_by_token.assert_awaited_once_with(
            token=workspace_invitation_token
        )
        if accept_workspace_invitation:
            fake_ws_invitations_services.accept_workspace_invitation_from_token.assert_awaited_once_with(
                token=workspace_invitation_token, user=user
            )
        else:
            fake_ws_invitations_services.accept_workspace_invitation_from_token.assert_not_awaited()

        fake_auth_services.create_auth_credentials.assert_awaited_once_with(user=user)


async def test_verify_user_error_with_invalid_data():
    with (
        patch("users.services.VerifyUserToken", autospec=True) as FakeVerifyUserToken,
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch_db_transaction(),
        pytest.raises(ex.BadVerifyUserTokenError),
    ):
        preserve_real_attrs(
            FakeVerifyUserToken.return_value.blacklist,
            VerifyUserToken.blacklist,
            ["__code__"],
        )
        fake_users_repo.get_user.side_effect = User.DoesNotExist

        await services.verify_user_from_token("some_token")


@pytest.mark.parametrize(
    "exception",
    [
        BadInvitationTokenError,
        ProjectInvitation.DoesNotExist,
    ],
)
async def test_verify_user_error_project_invitation_token(exception):
    user = f.build_user(is_active=False)
    project_invitation = f.build_project_invitation()
    project_invitation_token = "invitation_token"
    accept_project_invitation = False
    auth_credentials = TokenObtainPairOutputSchema(
        access="token", refresh="refresh", username=user.username
    )

    with (
        patch("users.services.VerifyUserToken", autospec=True) as FakeVerifyUserToken,
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch(
            "users.services.project_invitations_services", autospec=True
        ) as fake_invitations_services,
        patch("users.services.workspace_invitations_services", autospec=True),
        patch("users.services.auth_services", autospec=True) as fake_auth_services,
        patch_db_transaction(),
    ):
        FakeVerifyUserToken.return_value.get.side_effect = [
            1,
            None,
            project_invitation_token,
            accept_project_invitation,
        ]
        preserve_real_attrs(
            FakeVerifyUserToken.return_value.blacklist,
            VerifyUserToken.blacklist,
            ["__code__"],
        )
        fake_auth_services.create_auth_credentials.return_value = auth_credentials
        fake_invitations_services.get_project_invitation_by_token.return_value = (
            project_invitation
        )
        fake_users_repo.get_user.return_value = user

        #  exception when recovering the project invitation
        fake_invitations_services.get_project_invitation_by_token.side_effect = (
            exception
        )

        info = await services.verify_user_from_token("some_token")

        assert info.auth == auth_credentials
        # the exception is controlled returning no content (pass)
        assert info.project_invitation is None


@pytest.mark.parametrize(
    "exception",
    [
        BadInvitationTokenError,
        WorkspaceInvitation.DoesNotExist,
    ],
)
async def test_verify_user_error_workspace_invitation_token(exception):
    user = f.build_user(is_active=False)
    workspace_invitation = f.build_workspace_invitation()
    workspace_invitation_token = "invitation_token"
    accept_workspace_invitation = False
    auth_credentials = TokenObtainPairOutputSchema(
        access="token", refresh="refresh", username=user.username
    )

    with (
        patch("users.services.VerifyUserToken", autospec=True) as FakeVerifyUserToken,
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch("users.services.project_invitations_services", autospec=True),
        patch(
            "users.services.workspace_invitations_services", autospec=True
        ) as fake_invitations_services,
        patch("users.services.auth_services", autospec=True) as fake_auth_services,
        patch_db_transaction(),
    ):
        FakeVerifyUserToken.return_value.get.side_effect = [
            1,
            workspace_invitation_token,
            accept_workspace_invitation,
        ]
        preserve_real_attrs(
            FakeVerifyUserToken.return_value.blacklist,
            VerifyUserToken.blacklist,
            ["__code__"],
        )
        fake_auth_services.create_auth_credentials.return_value = auth_credentials
        fake_invitations_services.get_workspace_invitation_by_token.return_value = (
            workspace_invitation
        )
        fake_users_repo.get_user.return_value = user

        #  exception when recovering the workspace invitation
        fake_invitations_services.get_workspace_invitation_by_token.side_effect = (
            exception
        )

        info = await services.verify_user_from_token("some_token")

        assert info.auth == auth_credentials
        # the exception is controlled returning no content (pass)
        assert info.workspace_invitation is None


##########################################################
# _generate_verify_user_token
##########################################################


@pytest.mark.parametrize(
    "project_invitation_token, accept_project_invitation, expected_keys",
    [
        (
            "invitation_token",
            True,
            ["project_invitation_token", "accept_project_invitation"],
        ),
        ("invitation_token", False, ["project_invitation_token"]),
        (None, False, []),
    ],
)
async def test_generate_verify_ok_accept_project_invitation(
    project_invitation_token, accept_project_invitation, expected_keys
):
    user = f.build_user(is_active=False)
    token = {}

    with patch("users.services.VerifyUserToken", autospec=True) as FakeVerifyUserToken:
        FakeVerifyUserToken.for_user.return_value = token
        preserve_real_attrs(
            FakeVerifyUserToken.return_value.blacklist,
            VerifyUserToken.blacklist,
            ["__code__"],
        )

        verify_user_token_str = await services._generate_verify_user_token(
            user=user,
            project_invitation_token=project_invitation_token,
            accept_project_invitation=accept_project_invitation,
        )

        assert list(token.keys()) == expected_keys
        if "project_invitation_token" in list(token.keys()):
            assert token["project_invitation_token"] == project_invitation_token
        if "accept_project_invitation" in list(token.keys()):
            assert token["accept_project_invitation"] == accept_project_invitation
        assert str(token) == verify_user_token_str


##########################################################
# list_users_as_dict
##########################################################


async def test_list_users_as_dict_with_emails():
    user1 = f.build_user(email="one@tenzu.demo", username="one")
    user2 = f.build_user(email="two@tenzu.demo", username="two")
    user3 = f.build_user(email="three@tenzu.demo", username="three")

    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
    ):
        fake_users_repo.list_users.return_value = [user1, user2, user3]

        emails = [user1.email, user2.email, user3.email]
        users = await services.list_users_emails_as_dict(emails=emails)

        fake_users_repo.list_users.assert_called_once_with(
            filters={"is_active": True, "email__iin": emails}
        )
        assert users == {
            "one@tenzu.demo": user1,
            "two@tenzu.demo": user2,
            "three@tenzu.demo": user3,
        }


async def test_list_users_as_dict_with_usernames():
    user1 = f.build_user(email="one@tenzu.demo", username="one")
    user2 = f.build_user(email="two@tenzu.demo", username="two")
    user3 = f.build_user(email="three@tenzu.demo", username="three")

    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
    ):
        fake_users_repo.list_users.return_value = [user1, user2, user3]

        usernames = [user1.username, user2.username, user3.username]
        users = await services.list_users_usernames_as_dict(usernames=usernames)

        fake_users_repo.list_users.assert_called_once_with(
            filters={"is_active": True, "username__iin": usernames}
        )
        assert users == {"one": user1, "two": user2, "three": user3}


#####################################################################
# list_paginated_users_by_text (search users)
#####################################################################


async def test_list_paginated_project_users_by_text_ok():
    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
    ):
        fake_users_repo.list_project_users_by_text.return_value = []

        pagination, users = await services.list_paginated_users_by_text(
            text="text", project_id="id", offset=9, limit=10
        )

        fake_users_repo.list_project_users_by_text.assert_awaited_with(
            text_search="text", project_id="id", offset=9, limit=10
        )

        assert users == []


async def test_list_paginated_workspace_users_by_text_ok():
    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
    ):
        fake_users_repo.get_total_workspace_users_by_text.return_value = 0
        fake_users_repo.list_workspace_users_by_text.return_value = []

        pagination, users = await services.list_paginated_users_by_text(
            text="text", workspace_id="id", offset=9, limit=10
        )

        fake_users_repo.list_workspace_users_by_text.assert_awaited_with(
            text_search="text", workspace_id="id", offset=9, limit=10
        )

        assert users == []


async def test_list_paginated_default_project_users_by_text_ok():
    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
    ):
        fake_users_repo.list_project_users_by_text.return_value = []

        pagination, users = await services.list_paginated_users_by_text(
            text="text", offset=9, limit=10
        )

        fake_users_repo.list_project_users_by_text.assert_awaited_with(
            text_search="text", project_id=None, offset=9, limit=10
        )

        assert users == []


##########################################################
# update_user
##########################################################


async def test_update_user_ok(tqmanager):
    user = f.build_user(id=1, full_name="Full Name", lang="es-ES")
    new_full_name = "New Full Name"
    new_lang = "en-US"

    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
    ):
        await services.update_user(
            user=user, full_name=new_full_name, lang=new_lang, password=""
        )

        fake_users_repo.update_user.assert_awaited_once_with(
            user=user, values={"full_name": new_full_name, "lang": new_lang}
        )


#####################################################################
# delete user
#####################################################################


async def test_delete_user_success():
    user = f.build_user(username="user", is_active=True)
    user2 = f.build_user(username="user2", is_active=True)

    ws1 = f.build_workspace(created_by=user)
    ws2 = f.build_workspace(created_by=user)
    ws3 = f.build_workspace(created_by=user2)

    pj1_ws1 = f.build_project(workspace=ws1, created_by=user)
    pj2_ws1 = f.build_project(workspace=ws1, created_by=user)
    pj1_ws3 = f.build_project(workspace=ws3, created_by=user2)

    ws_member1_ws1 = f.build_workspace_membership(
        user=user, role__is_owner=True, workspace=ws1
    )
    ws_member1_ws2 = f.build_workspace_membership(
        user=user, role__is_owner=True, workspace=ws2
    )
    ws_member1_ws3 = f.build_workspace_membership(
        user=user, role__is_owner=False, workspace=ws3
    )

    inv1_ws3 = f.build_workspace_invitation(
        user=user, role__is_owner=False, workspace=ws3
    )

    pj_member1_pj1_ws1 = f.build_project_membership(
        user=user, role__is_owner=True, project=pj1_ws1
    )
    pj_member1_pj2_ws1 = f.build_project_membership(
        user=user, role__is_owner=True, project=pj2_ws1
    )
    pj_member1_pj1_ws3 = f.build_project_membership(
        user=user, role__is_owner=False, project=pj1_ws3
    )

    inv1_pj1_ws3 = f.build_project_invitation(
        user=user,
        role__is_owner=False,
        project=pj1_ws3,
        status=InvitationStatus.ACCEPTED,
    )

    with (
        patch(
            "users.services.ws_memberships_repositories", autospec=True
        ) as fake_ws_memberships_repositories,
        patch(
            "users.services.pj_memberships_repositories", autospec=True
        ) as fake_pj_memberships_repositories,
        patch(
            "users.services.projects_services", autospec=True
        ) as fake_projects_services,
        patch(
            "users.services.workspaces_repositories", autospec=True
        ) as fake_workspaces_repositories,
        patch(
            "users.services.ws_invitations_repositories", autospec=True
        ) as fake_ws_invitations_repositories,
        patch(
            "users.services.pj_invitations_repositories", autospec=True
        ) as fake_pj_invitations_repositories,
        patch(
            "users.services.users_repositories", autospec=True
        ) as fake_users_repositories,
        patch(
            "users.services.workspaces_events", autospec=True
        ) as fake_workspaces_events,
        patch(
            "users.services.ws_memberships_events", autospec=True
        ) as fake_ws_memberships_events,
        patch(
            "users.services.ws_invitations_events", autospec=True
        ) as fake_ws_invitations_events,
        patch(
            "users.services.pj_memberships_events", autospec=True
        ) as fake_pj_memberships_events,
        patch(
            "users.services.pj_invitations_events", autospec=True
        ) as fake_pj_invitations_events,
        patch("users.services.users_events", autospec=True) as fake_users_events,
        patch_db_transaction(),
    ):
        fake_ws_memberships_repositories.only_owner_queryset.return_value.aexists = (
            AsyncMock(return_value=False)
        )
        fake_pj_memberships_repositories.only_owner_queryset.return_value.aexists = (
            AsyncMock(return_value=False)
        )

        # projects where user is the only pj member
        fake_pj_memberships_repositories.only_project_member_queryset.return_value.select_related.return_value.__aiter__.return_value = [
            pj1_ws1,
            pj2_ws1,
            pj1_ws3,
        ]
        fake_projects_services.delete_project.return_value = True

        # workspaces where user is the only ws member
        fake_ws_memberships_repositories.only_workspace_member_queryset.return_value.__aiter__.return_value = [
            ws1,
            ws2,
        ]
        fake_workspaces_repositories.delete_workspace.return_value = 4

        fake_ws_memberships_repositories.list_memberships.return_value = [
            ws_member1_ws1,
            ws_member1_ws2,
            ws_member1_ws3,
        ]
        fake_ws_invitations_repositories.list_invitations.return_value = [inv1_ws3]
        fake_pj_memberships_repositories.list_memberships.return_value = [
            pj_member1_pj1_ws1,
            pj_member1_pj2_ws1,
            pj_member1_pj1_ws3,
        ]
        fake_pj_invitations_repositories.list_invitations.return_value = [inv1_pj1_ws3]

        fake_users_repositories.delete_user.return_value = 1

        deleted_user = await services.delete_user(user=user)

        # owner checks
        fake_ws_memberships_repositories.only_owner_queryset.assert_called_once_with(
            Workspace, user, is_collective=True
        )
        fake_pj_memberships_repositories.only_owner_queryset.assert_called_once_with(
            Project, user, is_collective=True
        )

        # projects deletion
        fake_pj_memberships_repositories.only_project_member_queryset.assert_called_once_with(
            user
        )
        fake_projects_services.delete_project.assert_any_await(
            project=pj1_ws1, deleted_by=user
        )
        fake_projects_services.delete_project.assert_any_await(
            project=pj2_ws1, deleted_by=user
        )
        fake_projects_services.delete_project.assert_any_await(
            project=pj1_ws3, deleted_by=user
        )

        # workspaces deletion
        fake_ws_memberships_repositories.only_workspace_member_queryset.assert_called_once_with(
            user
        )
        fake_workspaces_repositories.delete_workspace.assert_any_await(
            workspace_id=ws1.id
        )
        fake_workspaces_repositories.delete_workspace.assert_any_await(
            workspace_id=ws2.id
        )
        fake_workspaces_events.emit_event_when_workspace_is_deleted.assert_any_await(
            workspace=ws2, deleted_by=user
        )
        fake_workspaces_events.emit_event_when_workspace_is_deleted.assert_any_await(
            workspace=ws1, deleted_by=user
        )

        # ws memberships
        fake_ws_memberships_repositories.list_memberships.assert_awaited_once_with(
            WorkspaceMembership,
            filters={"user_id": user.id},
            select_related=["user", "workspace"],
        )
        fake_ws_memberships_events.emit_event_when_workspace_membership_is_deleted.assert_any_await(
            membership=ws_member1_ws1
        )
        fake_ws_memberships_events.emit_event_when_workspace_membership_is_deleted.assert_any_await(
            membership=ws_member1_ws2
        )
        fake_ws_memberships_events.emit_event_when_workspace_membership_is_deleted.assert_any_await(
            membership=ws_member1_ws3
        )

        # ws invitations
        fake_ws_invitations_repositories.list_invitations.assert_awaited_once_with(
            WorkspaceInvitation,
            filters={"user": user},
            select_related=["workspace"],
        )
        fake_ws_invitations_events.emit_event_when_workspace_invitation_is_deleted.assert_awaited_once_with(
            invitation_or_membership=inv1_ws3
        )

        # pj memberships
        fake_pj_memberships_repositories.list_memberships.assert_awaited_once_with(
            ProjectMembership,
            filters={"user_id": user.id},
            select_related=["user", "project"],
        )
        fake_pj_memberships_events.emit_event_when_project_membership_is_deleted.assert_any_await(
            membership=pj_member1_pj1_ws1, workspace_id=ws1.id
        )
        fake_pj_memberships_events.emit_event_when_project_membership_is_deleted.assert_any_await(
            membership=pj_member1_pj2_ws1, workspace_id=ws1.id
        )
        fake_pj_memberships_events.emit_event_when_project_membership_is_deleted.assert_any_await(
            membership=pj_member1_pj1_ws3, workspace_id=ws3.id
        )

        # pj invitations
        fake_pj_invitations_repositories.list_invitations.assert_awaited_once_with(
            ProjectInvitation,
            filters={"user": user},
            select_related=["project"],
        )
        fake_pj_invitations_events.emit_event_when_project_invitation_is_deleted.assert_awaited_once_with(
            invitation_or_membership=inv1_pj1_ws3, workspace_id=ws3.id
        )

        # user deleted
        fake_users_repositories.delete_user.assert_awaited_once_with(user)
        fake_users_events.emit_event_when_user_is_deleted.assert_awaited_once_with(
            user=user
        )
        assert deleted_user == 1


async def test_delete_user_error_only_owner():
    user = f.build_user(username="user", is_active=True)

    with (
        patch(
            "users.services.ws_memberships_repositories", autospec=True
        ) as fake_ws_memberships_repositories,
        patch(
            "users.services.pj_memberships_repositories", autospec=True
        ) as fake_pj_memberships_repositories,
        patch(
            "users.services.users_repositories", autospec=True
        ) as fake_users_repositories,
        patch_db_transaction(),
    ):
        with pytest.raises(MembershipIsTheOnlyOwnerError):
            fake_ws_memberships_repositories.only_owner_queryset.return_value.aexists = AsyncMock(
                return_value=True
            )
            await services.delete_user(user=user)
        with pytest.raises(MembershipIsTheOnlyOwnerError):
            fake_ws_memberships_repositories.only_owner_queryset.return_value.aexists = AsyncMock(
                return_value=False
            )
            fake_pj_memberships_repositories.only_owner_queryset.return_value.aexists = AsyncMock(
                return_value=True
            )
            await services.delete_user(user=user)

        fake_users_repositories.delete_user.assert_not_awaited()


#####################################################################
# reset password
#####################################################################


async def test_password_reset_ok():
    user = f.build_user(is_active=True)
    token_data = {"user_id": 1}

    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch(
            "users.services.ResetPasswordToken", autospec=True
        ) as FakeResetPasswordToken,
    ):
        FakeResetPasswordToken.return_value.payload = token_data
        preserve_real_attrs(
            FakeResetPasswordToken.return_value, ResetPasswordToken, ["get"]
        )
        preserve_real_attrs(
            FakeResetPasswordToken.return_value.blacklist,
            ResetPasswordToken.blacklist,
            ["__code__"],
        )
        fake_users_repo.get_user.return_value = user

        ret = await services._get_user_and_reset_password_token("")
        fake_users_repo.get_user.assert_awaited_once_with(
            filters={"id": token_data["user_id"], "is_active": True}
        )
        assert ret == (FakeResetPasswordToken(), user)


@pytest.mark.parametrize(
    "catched_ex, raised_ex",
    [
        (TokenError, ex.BadResetPasswordTokenError),
    ],
)
async def test_password_reset_error_token(catched_ex, raised_ex):
    with (
        patch(
            "users.services.ResetPasswordToken", autospec=True
        ) as FakeResetPasswordToken,
        pytest.raises(raised_ex),
    ):
        FakeResetPasswordToken.side_effect = catched_ex

        await services._get_user_and_reset_password_token("some_token")


async def test_password_reset_error_no_user_token():
    token_data = {"user_id": 1}

    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch(
            "users.services.ResetPasswordToken", autospec=True
        ) as FakeResetPasswordToken,
        pytest.raises(ex.BadResetPasswordTokenError),
    ):
        FakeResetPasswordToken.return_value.payload = token_data
        preserve_real_attrs(
            FakeResetPasswordToken.return_value, ResetPasswordToken, ["get"]
        )
        preserve_real_attrs(
            FakeResetPasswordToken.return_value.blacklist,
            ResetPasswordToken.blacklist,
            ["__code__"],
        )
        fake_users_repo.get_user.side_effect = User.DoesNotExist

        await services._get_user_and_reset_password_token("")
        FakeResetPasswordToken.return_value.blacklist.assert_called()


async def test_request_reset_password_ok():
    user = f.build_user(is_active=True)

    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch(
            "users.services._send_reset_password_email", return_value=None
        ) as fake_send_reset_password_email,
    ):
        fake_users_repo.get_user.return_value = user

        ret = await services.request_reset_password(user.email)

        fake_users_repo.get_user.assert_awaited_once_with(
            filters={"is_active": True},
            q_filter=fake_users_repo.username_or_email_query.return_value,
        )
        fake_users_repo.username_or_email_query.assert_called_once_with(user.email)
        fake_send_reset_password_email.assert_awaited_once_with(user)
        assert ret is None


async def test_request_reset_password_error_user():
    with (
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch(
            "users.services._send_reset_password_email", return_value=None
        ) as fake_send_reset_password_email,
    ):
        fake_users_repo.get_user.side_effect = User.DoesNotExist

        ret = await services.request_reset_password("user@email.com")

        fake_users_repo.get_user.assert_awaited_once()
        fake_send_reset_password_email.assert_not_awaited()
        assert ret is None


async def test_reset_password_send_reset_password_email_ok(tqmanager):
    user = f.build_user()

    with (
        patch(
            "users.services._generate_reset_password_token", return_value="reset_token"
        ) as fake_generate_reset_password_token,
    ):
        await services._send_reset_password_email(user=user)

        # assert len(tqmanager.pending_jobs) == 1
        # job = tqmanager.pending_jobs[0]
        # assert "send_email" in job["task_name"]
        # assert job["args"] == {
        #     "email_name": "reset_password",
        #     "to": user.email,
        #     "lang": "en-US",
        #     "context": {"reset_password_token": "reset_token"},
        # }

        fake_generate_reset_password_token.assert_awaited_once_with(user)


async def test_reset_password_generate_reset_password_token_ok():
    user = f.build_user()

    with (
        patch(
            "users.services.ResetPasswordToken", autospec=True
        ) as FakeResetPasswordToken,
    ):
        fake_token = FakeResetPasswordToken()
        FakeResetPasswordToken.for_user.return_value = fake_token

        ret = await services._generate_reset_password_token(user=user)
        FakeResetPasswordToken.for_user.assert_called_once_with(user)
        assert ret == str(fake_token)


async def test_verify_reset_password_token():
    user = f.build_user(is_active=True)

    with (
        patch(
            "users.services._get_user_and_reset_password_token", autospec=True
        ) as fake_get_user_and_reset_password_token,
        patch(
            "users.services.ResetPasswordToken", autospec=True
        ) as FakeResetPasswordToken,
    ):
        fake_token = FakeResetPasswordToken()
        fake_get_user_and_reset_password_token.return_value = (fake_token, user)

        ret = await services.verify_reset_password_token(fake_token)

        fake_get_user_and_reset_password_token.assert_awaited_once_with(fake_token)
        assert ret == bool((fake_token, user))


async def test_verify_reset_password_token_ok():
    user = f.build_user(is_active=True)

    with (
        patch(
            "users.services._get_user_and_reset_password_token", autospec=True
        ) as fake_get_user_and_reset_password_token,
        patch(
            "users.services.ResetPasswordToken", autospec=True
        ) as FakeResetPasswordToken,
    ):
        fake_token = FakeResetPasswordToken()
        fake_get_user_and_reset_password_token.return_value = (fake_token, user)

        ret = await services.verify_reset_password_token(fake_token)

        fake_get_user_and_reset_password_token.assert_awaited_once_with(fake_token)
        assert ret == bool((fake_token, user))


async def test_reset_password_ok_with_user():
    user = f.build_user(is_active=True)
    password = "password"

    with (
        patch(
            "users.services._get_user_and_reset_password_token", autospec=True
        ) as fake_get_user_and_reset_password_token,
        patch("users.services.users_repositories", autospec=True) as fake_users_repo,
        patch(
            "users.services.ResetPasswordToken", autospec=True
        ) as FakeResetPasswordToken,
    ):
        fake_token = FakeResetPasswordToken()
        fake_token.blacklist.return_value = None
        preserve_real_attrs(
            FakeResetPasswordToken.return_value.blacklist,
            ResetPasswordToken.blacklist,
            ["__code__"],
        )
        fake_get_user_and_reset_password_token.return_value = (fake_token, user)
        fake_users_repo.change_password.return_value = None

        ret = await services.reset_password(str(fake_token), password)

        fake_users_repo.change_password.assert_awaited_once_with(
            user=user, password=password
        )
        assert ret == user


async def test_reset_password_ok_without_user():
    password = "password"

    with (
        patch(
            "users.services._get_user_and_reset_password_token", autospec=True
        ) as fake_get_user_and_reset_password_token,
        patch(
            "users.services.ResetPasswordToken", autospec=True
        ) as FakeResetPasswordToken,
    ):
        fake_token = FakeResetPasswordToken()
        fake_token.blacklist.return_value = None
        fake_get_user_and_reset_password_token.return_value = (fake_token, None)

        ret = await services.reset_password(str(fake_token), password)

        assert ret is None


##########################################################
# misc - clean_expired_users
##########################################################


async def test_clean_expired_users():
    with patch("users.services.users_repositories", autospec=True) as fake_users_repo:
        await services.clean_expired_users()
        fake_users_repo.clean_expired_users.assert_awaited_once()

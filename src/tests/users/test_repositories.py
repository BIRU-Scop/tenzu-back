# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 BIRU
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
from django.db import IntegrityError
from django.test import override_settings

from memberships.choices import InvitationStatus
from ninja_jwt.utils import aware_utcnow
from projects.projects.models import ProjectTemplate
from tests.utils import factories as f
from users import repositories as users_repositories
from users.models import User
from users.tokens import VerifyUserToken

pytestmark = pytest.mark.django_db


##########################################################
# create_user
##########################################################


async def test_create_user_success():
    email = "EMAIL@email.com"
    full_name = "Full Name"
    color = 8
    password = "password"
    lang = "es-es"
    acceptance_date = aware_utcnow()
    user = await users_repositories.create_user(
        email=email,
        full_name=full_name,
        color=color,
        password=password,
        lang=lang,
        acceptance_date=acceptance_date,
    )
    await user.arefresh_from_db()
    assert user.email == email.lower()
    assert user.username == "email"
    assert user.password
    assert user.lang == lang


async def test_create_user_not_accepted_terms():
    email = "EMAIL@email.com"
    full_name = "Full Name"
    password = "password"
    lang = "es-es"
    color = 1
    acceptance_date = None

    with pytest.raises(ValueError):
        await users_repositories.create_user(
            email=email.upper(),
            full_name=full_name,
            password=password,
            lang=lang,
            color=color,
            acceptance_date=acceptance_date,
        )


async def test_create_user_error_email_or_username_case_insensitive():
    email = "EMAIL@email.com"
    full_name = "Full Name"
    password = "password"
    lang = "es-es"
    color = 1
    acceptance_date = aware_utcnow()

    await users_repositories.create_user(
        email=email,
        full_name=full_name,
        password=password,
        lang=lang,
        color=color,
        acceptance_date=acceptance_date,
    )

    with pytest.raises(IntegrityError):
        await users_repositories.create_user(
            email=email.upper(),
            full_name=full_name,
            password=password,
            lang=lang,
            color=color,
            acceptance_date=acceptance_date,
        )


@override_settings(REQUIRED_TERMS=False)
async def test_create_user_no_password_from_social():
    email = "EMAIL@email.com"
    full_name = "Full Name"
    password = None
    lang = "es-es"
    color = 1
    acceptance_date = None

    res = await users_repositories.create_user(
        email=email,
        full_name=full_name,
        password=password,
        lang=lang,
        color=color,
        acceptance_date=acceptance_date,
    )

    assert not res.has_usable_password()


##########################################################
# list_users
##########################################################


async def test_list_users_by_usernames():
    user1 = await f.create_user()
    user2 = await f.create_user()
    user3 = await f.create_user(is_active=False)

    users = await users_repositories.list_users(
        filters={
            "is_active": True,
            "username__iin": [user1.username, user2.username, user3.username],
        }
    )

    assert len(users) == 2
    assert user3 not in users


async def test_list_users_by_emails():
    user1 = await f.create_user()
    user2 = await f.create_user()
    user3 = await f.create_user(is_active=False)

    users = await users_repositories.list_users(
        filters={
            "is_active": True,
            "email__iin": [user1.email, user2.email, user3.email],
        }
    )

    assert len(users) == 2
    assert user3 not in users


##########################################################
# list_project_users_by_text
##########################################################


@pytest.fixture
async def _setup_user_text_search_data(db):
    class DummyObject:
        pass

    data = DummyObject()
    data.ws_pj_admin = await f.create_user(
        is_active=True, username="wsadmin", full_name="ws-pj-admin"
    )
    data.elettescar = await f.create_user(
        is_active=True, username="elettescar", full_name="Elettescar - ws member"
    )
    data.electra = await f.create_user(
        is_active=True, username="electra", full_name="Electra - pj member"
    )
    data.danvers = await f.create_user(
        is_active=True, username="danvers", full_name="Danvers elena"
    )
    await f.create_user(is_active=True, username="edanvers", full_name="Elena Danvers")
    await f.create_user(is_active=True, username="elmary", full_name="Él Marinari")
    data.storm = await f.create_user(
        is_active=True, username="storm", full_name="Storm Smith"
    )
    data.inactive_user = await f.create_user(
        is_active=False, username="inactive", full_name="Inactive User"
    )

    # elettescar is ws-member
    data.workspace = await f.create_workspace(created_by=data.ws_pj_admin, color=2)
    data.general_workspace_role = await f.create_workspace_role(
        workspace=data.workspace, is_owner=False
    )
    await f.create_workspace_membership(
        user=data.elettescar,
        workspace=data.workspace,
        role=data.general_workspace_role,
    )

    # electra is a pj-member (from the previous workspace)
    data.project = await f.create_project(
        template=await ProjectTemplate.objects.afirst(),
        workspace=data.workspace,
        created_by=data.ws_pj_admin,
    )
    data.general_role = await f.create_project_role(
        project=data.project, is_owner=False
    )
    await f.create_project_membership(
        user=data.electra, project=data.project, role=data.general_role
    )

    # danvers has a pending invitation
    await f.create_project_invitation(
        email="danvers@email.com",
        user=data.danvers,
        project=data.project,
        role=data.general_role,
        status=InvitationStatus.PENDING,
        invited_by=data.ws_pj_admin,
    )
    return data


async def test_list_project_users_no_filter(_setup_user_text_search_data):
    # searching all but inactive or system users (no text or project specified).
    # results returned by alphabetical order (full_name/username)
    all_active_no_sys_users_result = (
        await users_repositories.list_project_users_by_text()
    )
    assert len(all_active_no_sys_users_result) == 7
    assert all_active_no_sys_users_result[0].full_name == "Danvers elena"
    assert all_active_no_sys_users_result[1].full_name == "Electra - pj member"
    assert all_active_no_sys_users_result[2].full_name == "Elena Danvers"
    assert (
        _setup_user_text_search_data.inactive_user not in all_active_no_sys_users_result
    )


async def test_list_project_users_ordering(_setup_user_text_search_data):
    # searching for project, no text search. Ordering by project closeness and alphabetically (full_name/username)
    result = await users_repositories.list_project_users_by_text(
        project_id=_setup_user_text_search_data.project.id
    )
    assert len(result) == 7
    # pj members should be returned first (project closeness criteria)
    assert result[0].full_name == "Electra - pj member"
    assert result[0].user_is_member is True
    assert result[0].user_has_pending_invitation is False
    assert result[1].full_name == "ws-pj-admin"
    assert result[1].user_is_member is True
    assert result[1].user_has_pending_invitation is False
    # ws members should be returned secondly
    assert result[2].full_name == "Elettescar - ws member"
    assert result[2].user_is_member is False
    assert result[2].user_has_pending_invitation is False
    # then the rest of users alphabetically
    assert result[3].full_name == "Danvers elena"
    assert result[3].user_is_member is False
    assert result[3].user_has_pending_invitation is True
    assert result[4].full_name == "Elena Danvers"
    assert result[5].full_name == "Él Marinari"
    assert result[6].full_name == "Storm Smith"

    assert _setup_user_text_search_data.inactive_user not in result


async def test_list_project_users_by_text_lower_case(_setup_user_text_search_data):
    # searching for a text containing several words in lower case
    result = await users_repositories.list_project_users_by_text(
        text_search="storm smith"
    )
    assert len(result) == 1
    assert result[0].full_name == "Storm Smith"


async def test_list_project_users_by_text_special_chars(_setup_user_text_search_data):
    # searching for texts containing special chars (and cause no exception)
    result = await users_repositories.list_project_users_by_text(text_search="<")
    assert len(result) == 0


async def test_list_project_users_text_weights(_setup_user_text_search_data):
    # Paginated search according to search text weights.
    # 1st order by project closeness (pj, ws, others), 2nd by text search order (rank, left match)
    result = await users_repositories.list_project_users_by_text(
        text_search="EL",
        project_id=_setup_user_text_search_data.project.id,
        offset=0,
        limit=4,
    )
    assert len(result) == 4
    # first result must be `electra` as a pj-member (no matter how low her rank is against other farther pj users)
    assert result[0].full_name == "Electra - pj member"
    # second result should be `elettescar` as ws-member matching the text
    assert result[1].full_name == "Elettescar - ws member"
    # then the rest of users alphabetically ordered by rank and alphabetically.
    # first would be *Él* Marinari/*el*mary with the highest rank (0.6079)
    assert result[2].full_name == "Él Marinari"
    # then goes `Elena Danvers` with a tied second rank (0.3039) but her name starts with the searched text ('el')
    assert result[3].full_name == "Elena Danvers"
    # `Danvers Elena` has the same rank (0.3039) but his name doesn't start with 'el', so he's left outside from the
    # results due to the pagination limit (4)
    assert _setup_user_text_search_data.danvers not in result
    assert _setup_user_text_search_data.inactive_user not in result
    assert _setup_user_text_search_data.ws_pj_admin not in result
    assert _setup_user_text_search_data.storm not in result


##########################################################
# list_workspace_users_by_text
##########################################################


async def test_list_workspace_users_by_workspace(_setup_user_text_search_data):
    # workspace search, no text search. Ordering by workspace closeness and alphabetically (full_name/username)
    result = await users_repositories.list_workspace_users_by_text(
        workspace_id=_setup_user_text_search_data.workspace.id
    )
    assert len(result) == 7
    # ws members should be returned first (workspace closeness criteria)
    assert result[0].full_name == "Elettescar - ws member"
    assert result[0].user_is_member is True
    assert result[0].user_has_pending_invitation is False
    assert result[1].full_name == "ws-pj-admin"
    assert result[1].user_is_member is True
    assert result[1].user_has_pending_invitation is False
    # any member of the workspace's projects should be returned secondly
    assert result[2].full_name == "Electra - pj member"
    assert result[2].user_is_member is False
    assert result[2].user_has_pending_invitation is False
    # then the rest of users alphabetically
    assert result[3].full_name == "Danvers elena"
    assert result[3].user_is_member is False
    assert result[3].user_has_pending_invitation is False
    assert result[4].full_name == "Elena Danvers"
    assert result[5].full_name == "Él Marinari"
    assert result[6].full_name == "Storm Smith"

    assert _setup_user_text_search_data.inactive_user not in result


async def test_list_workspace_users_by_text_lower_case(_setup_user_text_search_data):
    # searching for a text containing several words in lower case
    result = await users_repositories.list_workspace_users_by_text(
        text_search="storm smith",
        workspace_id=_setup_user_text_search_data.workspace.id,
    )
    assert len(result) == 1
    assert result[0].full_name == "Storm Smith"


async def test_list_workspace_users_by_text_special_chars(_setup_user_text_search_data):
    # searching for texts containing special chars (and cause no exception)
    result = await users_repositories.list_workspace_users_by_text(
        text_search="<", workspace_id=_setup_user_text_search_data.workspace.id
    )
    assert len(result) == 0


async def test_list_workspace_users_text_weights(_setup_user_text_search_data):
    # Paginated search according to search text weights.
    # 1st order by workspace closeness (ws, ws'pj membership, others), 2nd by text search order (rank, left match)
    result = await users_repositories.list_workspace_users_by_text(
        text_search="EL",
        workspace_id=_setup_user_text_search_data.workspace.id,
        offset=0,
        limit=4,
    )
    assert len(result) == 4
    # first result must be 'elettescar' as the only ws-member matching the text
    assert result[0].full_name == "Elettescar - ws member"
    # second result should be `electra` as the only member of the workspace's projects matching the text
    assert result[1].full_name == "Electra - pj member"
    # then the rest of users alphabetically ordered by rank and alphabetically, always matching the text.
    # first would be *Él* Marinari/*el*mary with the highest rank (0.6079)
    assert result[2].full_name == "Él Marinari"
    # then goes `Elena Danvers` with a tied second rank (0.3039) but her name starts with the searched text ('el')
    assert result[3].full_name == "Elena Danvers"
    # `Danvers Elena` has the same rank (0.3039) but his name doesn't start with 'el', so he's left outside from the
    # results due to the pagination limit (4)
    assert _setup_user_text_search_data.danvers not in result
    assert _setup_user_text_search_data.inactive_user not in result
    assert _setup_user_text_search_data.ws_pj_admin not in result
    assert _setup_user_text_search_data.storm not in result


##########################################################
# get_user
##########################################################


async def test_get_user_by_username_or_email_success_username_case_insensitive():
    user = await f.create_user(username="test_user_1")
    await f.create_user(username="test_user_2")
    assert user == await users_repositories.get_user(
        q_filter=users_repositories.username_or_email_query("test_user_1")
    )
    assert user == await users_repositories.get_user(
        q_filter=users_repositories.username_or_email_query("TEST_user_1")
    )


async def test_get_user_by_username_or_email_error_invalid_username_case_insensitive():
    with pytest.raises(User.DoesNotExist):
        await users_repositories.get_user(
            q_filter=users_repositories.username_or_email_query("test_other_user")
        )


async def test_get_user_by_username_or_email_success_email_case_insensitive():
    user = await f.create_user(email="test_user_1@email.com")
    await f.create_user(email="test_user_2@email.com")
    assert user == await users_repositories.get_user(
        q_filter=users_repositories.username_or_email_query("test_user_1@email.com")
    )
    assert user == await users_repositories.get_user(
        q_filter=users_repositories.username_or_email_query("TEST_user_1@email.com")
    )


async def test_get_user_by_username_or_email_error_invalid_email_case_insensitive():
    with pytest.raises(User.DoesNotExist):
        await users_repositories.get_user(
            q_filter=users_repositories.username_or_email_query(
                "test_other_user@email.com"
            )
        )


async def test_get_user_by_email():
    user = await f.create_user()
    assert user == await users_repositories.get_user(filters={"email": user.email})


async def test_get_user_by_uuid():
    user = await f.create_user()
    assert user == await users_repositories.get_user(filters={"id": user.id})


##########################################################
# update_user
##########################################################


async def test_update_user():
    user = await f.create_user(username="old_username")
    assert user.username == "old_username"
    updated_user = await users_repositories.update_user(
        user=user,
        values={"username": "new_username"},
    )
    assert updated_user.username == "new_username"


##########################################################
# delete_user
##########################################################


async def test_delete_user():
    user = await f.create_user(username="user", is_active=True)

    deleted = await users_repositories.delete_user(user)
    assert deleted == 1


##########################################################
# misc - check_password / change_password
##########################################################


async def test_change_password_and_check_password():
    password1 = "password-one"
    password2 = "password-two"
    user = await f.create_user(password=password1)

    assert await users_repositories.check_password(user, password1)
    assert not await users_repositories.check_password(user, password2)

    await users_repositories.change_password(user, password2)

    assert not await users_repositories.check_password(user, password1)
    assert await users_repositories.check_password(user, password2)


##########################################################
# misc - clean_expired_users
##########################################################


async def test_clean_expired_users():
    total_users = await User.objects.acount()
    await f.create_user(is_active=False)  # without token - it'll be cleaned
    user = await f.create_user(is_active=False)  # with token - it won't be cleaned
    await sync_to_async(VerifyUserToken.for_user)(user)

    assert await User.objects.acount() == total_users + 2
    await users_repositories.clean_expired_users()
    assert await User.objects.acount() == total_users + 1

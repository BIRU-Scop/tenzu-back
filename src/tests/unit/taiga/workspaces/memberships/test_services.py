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

from unittest.mock import patch
from uuid import uuid1

import pytest

from tests.utils import factories as f
from workspaces.memberships import services
from workspaces.memberships.services import (
    WS_ROLE_NAME_GUEST,
    WS_ROLE_NAME_MEMBER,
    WS_ROLE_NAME_NONE,
)
from workspaces.memberships.services import exceptions as ex

pytestmark = pytest.mark.django_db


#######################################################
# list_workspace_memberships
#######################################################


async def test_list_workspace_memberships():
    user = await f.create_user()
    workspace = await f.create_workspace()
    workspace_membership = await f.create_workspace_membership(
        user=user, workspace=workspace
    )
    project = await f.create_project(workspace=workspace)

    with (
        patch(
            "workspaces.memberships.services.serializer_services", autospec=True
        ) as fake_serializer_services,
        patch(
            "workspaces.memberships.services.projects_repositories", autospec=True
        ) as fake_pj_repositories,
        patch(
            "workspaces.memberships.services.workspace_memberships_repositories",
            autospec=True,
        ) as fake_ws_membership_repository,
    ):
        fake_ws_membership_repository.list_workspace_memberships.return_value = [
            workspace_membership
        ]
        fake_pj_repositories.list_projects.return_value = [project]

        await services.list_workspace_memberships(workspace=workspace)
        fake_ws_membership_repository.list_workspace_memberships.assert_awaited_once_with(
            filters={"workspace_id": workspace.id},
            select_related=["user", "workspace"],
        )
        fake_serializer_services.serialize_workspace_membership_detail.assert_called_once_with(
            ws_membership=workspace_membership,
            projects=[project],
        )
        fake_pj_repositories.list_projects.assert_awaited_once_with(
            filters={"workspace_id": workspace.id, "memberships__user_id": user.id}
        )


async def test_list_paginated_workspace_guests():
    user = await f.create_user()
    workspace = await f.create_workspace()
    project = await f.create_project(
        created_by=workspace.created_by, workspace=workspace
    )
    await f.create_project_membership(user=user, project=project)
    offset = 0
    limit = 10

    with (
        patch(
            "workspaces.memberships.services.users_repositories", autospec=True
        ) as fake_users_repos,
        patch(
            "workspaces.memberships.services.serializer_services", autospec=True
        ) as fake_serializer_services,
        patch(
            "workspaces.memberships.services.projects_repositories", autospec=True
        ) as fake_pj_repositories,
    ):
        fake_users_repos.list_users.return_value = [user]
        fake_users_repos.get_total_users.return_value = 1
        fake_pj_repositories.list_projects.return_value = [project]

        await services.list_paginated_workspace_guests(
            workspace=workspace, offset=offset, limit=limit
        )
        fake_users_repos.list_users.assert_awaited_once_with(
            filters={"guests_in_workspace": workspace},
            offset=offset,
            limit=limit,
        )
        fake_users_repos.get_total_users.assert_awaited_once_with(
            filters={"guests_in_workspace": workspace},
        )
        fake_serializer_services.serialize_workspace_guest_detail.assert_called_once_with(
            user=user,
            projects=[project],
        )
        fake_pj_repositories.list_projects.assert_awaited_once_with(
            filters={"workspace_id": workspace.id, "memberships__user_id": user.id}
        )


##########################################################
# delete workspace membership
##########################################################


async def test_delete_workspace_membership():
    workspace = f.build_workspace()
    user = f.build_user()
    membership = f.build_workspace_membership(workspace=workspace, user=user)

    with (
        patch(
            "workspaces.memberships.services.workspace_memberships_repositories",
            autospec=True,
        ) as fake_ws_memberships_repo,
        patch(
            "workspaces.memberships.services.workspace_invitations_repositories",
            autospec=True,
        ) as fake_ws_invitations_repo,
        patch(
            "workspaces.memberships.services.workspace_memberships_events",
            autospec=True,
        ) as fake_ws_memberships_events,
    ):
        fake_ws_memberships_repo.get_total_workspace_memberships.return_value = 2
        fake_ws_memberships_repo.delete_workspace_memberships.return_value = 1

        await services.delete_workspace_membership(membership=membership)

        fake_ws_memberships_repo.get_total_workspace_memberships.assert_awaited_once_with(
            filters={"workspace_id": workspace.id},
        )
        fake_ws_memberships_repo.delete_workspace_memberships.assert_awaited_once_with(
            filters={"id": membership.id},
        )
        fake_ws_invitations_repo.delete_workspace_invitation.assert_awaited_once_with(
            filters={
                "workspace_id": workspace.id,
                "username_or_email": membership.user.email,
            },
        )
        fake_ws_memberships_events.emit_event_when_workspace_membership_is_deleted.assert_awaited_once_with(
            membership=membership
        )


async def test_delete_workspace_latest_membership():
    workspace = f.build_workspace()
    user = f.build_user()
    membership = f.build_workspace_membership(workspace=workspace, user=user)

    with (
        patch(
            "workspaces.memberships.services.workspace_memberships_repositories",
            autospec=True,
        ) as fake_ws_memberships_repo,
        patch(
            "workspaces.memberships.services.workspace_memberships_events",
            autospec=True,
        ) as fake_ws_memberships_events,
        pytest.raises(ex.MembershipIsTheOnlyMemberError),
    ):
        fake_ws_memberships_repo.get_total_workspace_memberships.return_value = 1

        await services.delete_workspace_membership(membership=membership)

        fake_ws_memberships_repo.get_total_workspace_memberships.assert_awaited_once_with(
            filters={"workspace_id": workspace.id},
        )
        fake_ws_memberships_repo.delete_workspace_memberships.assert_not_awaited()
        fake_ws_memberships_events.emit_event_when_workspace_membership_is_deleted.assert_not_awaited()


##########################################################
# misc - get_workspace_role_name
##########################################################


async def test_get_workspace_role_name_with_admin_user():
    workspace_id = uuid1()
    user_id = uuid1()
    with (
        patch(
            "workspaces.memberships.services.workspace_memberships_repositories",
            autospec=True,
        ) as fake_ws_memberships_repo,
    ):
        fake_ws_memberships_repo.get_workspace_membership.return_value = (
            "Workspace membership"
        )
        ret = await services.get_workspace_role_name(
            workspace_id=workspace_id, user_id=user_id
        )

        fake_ws_memberships_repo.get_workspace_membership.assert_awaited_once_with(
            filters={"workspace_id": workspace_id, "user_id": user_id}
        )
        assert ret is WS_ROLE_NAME_MEMBER


async def test_get_workspace_role_name_with_guest_user():
    workspace_id = uuid1()
    user_id = uuid1()
    with (
        patch(
            "workspaces.memberships.services.workspace_memberships_repositories",
            autospec=True,
        ) as fake_ws_memberships_repo,
        patch(
            "workspaces.memberships.services.projects_memberships_repositories",
            autospec=True,
        ) as fake_pj_memberships_repo,
    ):
        fake_ws_memberships_repo.get_workspace_membership.return_value = None
        fake_pj_memberships_repo.exist_project_membership.return_value = True
        ret = await services.get_workspace_role_name(
            workspace_id=workspace_id, user_id=user_id
        )

        fake_ws_memberships_repo.get_workspace_membership.assert_awaited_once_with(
            filters={"workspace_id": workspace_id, "user_id": user_id}
        )
        fake_pj_memberships_repo.exist_project_membership.assert_awaited_once_with(
            filters={"user_id": user_id, "workspace_id": workspace_id}
        )
        assert ret is WS_ROLE_NAME_GUEST


async def test_get_workspace_role_name_with_no_related_user():
    workspace_id = uuid1()
    user_id = uuid1()
    with (
        patch(
            "workspaces.memberships.services.workspace_memberships_repositories",
            autospec=True,
        ) as fake_ws_memberships_repo,
        patch(
            "workspaces.memberships.services.projects_memberships_repositories",
            autospec=True,
        ) as fake_pj_memberships_repo,
    ):
        fake_ws_memberships_repo.get_workspace_membership.return_value = None
        fake_pj_memberships_repo.exist_project_membership.return_value = False
        ret = await services.get_workspace_role_name(
            workspace_id=workspace_id, user_id=user_id
        )

        fake_ws_memberships_repo.get_workspace_membership.assert_awaited_once_with(
            filters={"workspace_id": workspace_id, "user_id": user_id}
        )
        fake_pj_memberships_repo.exist_project_membership.assert_awaited_once_with(
            filters={"user_id": user_id, "workspace_id": workspace_id}
        )
        assert ret is WS_ROLE_NAME_NONE


async def test_get_workspace_role_name_with_no_user():
    workspace_id = uuid1()
    user_id = None
    ret = await services.get_workspace_role_name(
        workspace_id=workspace_id, user_id=user_id
    )

    assert ret is WS_ROLE_NAME_NONE

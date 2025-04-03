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

import pytest

from memberships.services import exceptions as ex
from tests.utils import factories as f
from workspaces.memberships import services
from workspaces.memberships.models import WorkspaceRole

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
# misc - get_workspace_role
##########################################################


async def test_get_workspace_role():
    workspace = f.build_workspace()
    role = f.build_workspace_role(workspace=workspace)
    with (
        patch(
            "workspaces.memberships.services.workspace_memberships_repositories",
            autospec=True,
        ) as fake_ws_memberships_repo,
    ):
        fake_ws_memberships_repo.get_role.return_value = role
        ret = await services.get_workspace_role(
            workspace_id=workspace.id, slug=role.slug
        )

        fake_ws_memberships_repo.get_role.assert_awaited_once_with(
            WorkspaceRole,
            filters={"workspace_id": workspace.id, "slug": role.slug},
            select_related=["workspace"],
        )
        assert ret == role

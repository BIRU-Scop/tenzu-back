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

from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID
from tests.utils.utils import patch_db_transaction
from workspaces.workspaces import services
from workspaces.workspaces.services import exceptions as ex

##########################################################
# create_workspace
##########################################################


async def test_create_workspace_ok():
    user = f.build_user()
    name = "workspace1"
    color = 5
    with (
        patch(
            "workspaces.workspaces.services.workspaces_repositories", autospec=True
        ) as fake_workspaces_repo,
        patch(
            "workspaces.workspaces.services.ws_memberships_repositories", autospec=True
        ) as fake_ws_memberships_repo,
        patch(
            "workspaces.workspaces.services.WorkspaceDetailSerializer", autospec=True
        ) as fake_WorkspaceDetailSerializer,
        patch(
            "workspaces.workspaces.services.workspaces_events", autospec=True
        ) as fake_workspaces_events,
        patch_db_transaction(),
    ):
        await services.create_workspace(name=name, color=color, created_by=user)
        fake_workspaces_repo.create_workspace.assert_awaited_once()
        fake_ws_memberships_repo.create_workspace_membership.assert_awaited_once()
        fake_workspaces_events.emit_event_when_workspace_is_created.assert_awaited_once_with(
            workspace_detail=fake_WorkspaceDetailSerializer.return_value,
            created_by=user,
        )
        assert (
            fake_WorkspaceDetailSerializer.call_args.kwargs["user_is_invited"] is False
        )
        assert fake_WorkspaceDetailSerializer.call_args.kwargs["user_is_member"] is True
        assert (
            fake_WorkspaceDetailSerializer.call_args.kwargs["user_can_create_projects"]
            is True
        )
        assert fake_WorkspaceDetailSerializer.call_args.kwargs["total_projects"] == 0


##########################################################
# list_user_workspaces
##########################################################


async def test_list_user_workspaces():
    user = f.build_user()

    with patch(
        "workspaces.workspaces.services.workspaces_repositories", autospec=True
    ) as fake_workspaces_repo:
        await services.list_user_workspaces(user=user)
        fake_workspaces_repo.list_user_workspaces_overview.assert_awaited_once_with(
            user=user
        )


##########################################################
# get_workspace
##########################################################


async def test_get_workspace():
    with patch(
        "workspaces.workspaces.services.workspaces_repositories", autospec=True
    ) as fake_workspaces_repo:
        await services.get_workspace(workspace_id=NOT_EXISTING_UUID)
        fake_workspaces_repo.get_workspace.assert_awaited_with(
            workspace_id=NOT_EXISTING_UUID, get_total_project=False
        )


##########################################################
# get_user_workspace
##########################################################


async def test_get_user_workspace():
    workspace = f.build_workspace(name="test")
    workspace.total_projects = 3
    user = f.build_user()
    role = f.build_workspace_role(workspace=workspace)
    user.workspace_role = role

    with (
        patch(
            "workspaces.workspaces.services.WorkspaceDetailSerializer", autospec=True
        ) as fake_WorkspaceDetailSerializer,
    ):
        await services.get_user_workspace(workspace=workspace, user=user)
        fake_WorkspaceDetailSerializer.assert_called_with(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            color=workspace.color,
            user_role=role,
            user_is_invited=False,
            user_is_member=True,
            user_can_create_projects=True,
            total_projects=3,
        )


##########################################################
# update_workspace
##########################################################


async def test_update_workspace_ok(tqmanager):
    workspace = f.build_workspace()
    user = f.build_user()
    values = {"name": "new name"}
    user.workspace_role = None
    workspace.total_projects = 3

    with (
        patch(
            "workspaces.workspaces.services.workspaces_repositories", autospec=True
        ) as fake_workspaces_repo,
        patch(
            "workspaces.workspaces.services.WorkspaceDetailSerializer"
        ) as fake_WorkspaceDetailSerializer,
        patch(
            "workspaces.workspaces.services.workspaces_events", autospec=True
        ) as fake_projects_events,
    ):
        fake_workspaces_repo.update_workspace.return_value = workspace
        await services.update_workspace(workspace=workspace, user=user, values=values)
        fake_workspaces_repo.update_workspace.assert_awaited_once_with(
            workspace=workspace, values=values
        )
        assert len(tqmanager.pending_jobs) == 0
        fake_WorkspaceDetailSerializer.assert_called_with(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            color=workspace.color,
            user_role=None,
            user_is_invited=False,
            user_is_member=False,
            user_can_create_projects=False,
            total_projects=3,
        )
        fake_projects_events.emit_event_when_workspace_is_updated.assert_awaited_once_with(
            workspace_detail=fake_WorkspaceDetailSerializer.return_value,
            updated_by=user,
        )


##########################################################
# delete_workspace
##########################################################


async def test_delete_workspace_without_projects():
    workspace = f.build_workspace()

    with (
        patch(
            "workspaces.workspaces.services.workspaces_repositories", autospec=True
        ) as fake_workspaces_repo,
        patch(
            "workspaces.workspaces.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
        patch(
            "workspaces.workspaces.services.workspaces_events", autospec=True
        ) as fake_workspaces_events,
    ):
        fake_projects_repo.get_total_projects.return_value = 0
        fake_workspaces_repo.delete_workspace.return_value = 4

        ret = await services.delete_workspace(
            workspace=workspace, deleted_by=workspace.created_by
        )

        fake_projects_repo.get_total_projects.assert_awaited_with(
            workspace_id=workspace.id
        )
        fake_workspaces_repo.delete_workspace.assert_awaited_with(
            workspace_id=workspace.id
        )
        fake_workspaces_events.emit_event_when_workspace_is_deleted.assert_awaited()
        assert ret is True


async def test_delete_workspace_with_projects():
    workspace = f.build_workspace()

    with (
        patch(
            "workspaces.workspaces.services.workspaces_repositories", autospec=True
        ) as fake_workspaces_repo,
        patch(
            "workspaces.workspaces.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
        patch(
            "workspaces.workspaces.services.workspaces_events", autospec=True
        ) as fake_workspaces_events,
        pytest.raises(ex.WorkspaceHasProjects),
    ):
        fake_projects_repo.get_total_projects.return_value = 1
        await services.delete_workspace(
            workspace=workspace, deleted_by=workspace.created_by
        )

        fake_workspaces_repo.delete_workspace.assert_not_awaited()
        fake_workspaces_events.emit_event_when_workspace_is_deleted.assert_not_awaited()


async def test_delete_workspace_not_deleted_in_db():
    workspace = f.build_workspace()

    with (
        patch(
            "workspaces.workspaces.services.workspaces_repositories", autospec=True
        ) as fake_workspaces_repo,
        patch(
            "workspaces.workspaces.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
        patch(
            "workspaces.workspaces.services.workspaces_events", autospec=True
        ) as fake_workspaces_events,
    ):
        fake_projects_repo.get_total_projects.return_value = 0
        fake_workspaces_repo.delete_workspace.return_value = 0
        ret = await services.delete_workspace(
            workspace=workspace, deleted_by=workspace.created_by
        )

        fake_projects_repo.get_total_projects.assert_awaited_with(
            workspace_id=workspace.id
        )
        fake_workspaces_repo.delete_workspace.assert_awaited_with(
            workspace_id=workspace.id
        )
        fake_workspaces_events.emit_event_when_workspace_is_deleted.assert_not_awaited()

        assert ret is False

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
from unittest.mock import patch

import pytest

from tests.utils import factories as f
from workspaces.workspaces import services
from workspaces.workspaces.services import exceptions as ex

pytestmark = pytest.mark.django_db


##########################################################
# create_workspace
##########################################################


async def test_create_workspace():
    user = await f.create_user()
    name = "workspace1"
    color = 5
    with (
        patch(
            "workspaces.workspaces.services.workspaces_repositories", autospec=True
        ) as fake_workspaces_repo,
        patch(
            "workspaces.workspaces.services.ws_memberships_repositories", autospec=True
        ) as fake_ws_memberships_repo,
    ):
        await services._create_workspace(name=name, color=color, created_by=user)
        fake_workspaces_repo.create_workspace.assert_awaited_once()
        fake_ws_memberships_repo.create_workspace_membership.assert_awaited_once()


async def test_create_workspace_detail():
    workspace = await f.create_workspace()
    user = await f.create_user()
    name = "workspace1"
    color = 5
    with (
        patch(
            "workspaces.workspaces.services._create_workspace",
            return_value=workspace,
            autospec=True,
        ) as fake_create_method,
        patch(
            "workspaces.workspaces.services.get_workspace_detail", autospec=True
        ) as fake_serializer_method,
    ):
        fake_create_method.return_value = workspace
        await services.create_workspace(name=name, color=color, created_by=user)
        fake_create_method.assert_awaited_with(name=name, color=color, created_by=user)
        fake_serializer_method.assert_awaited_with(id=workspace.id, user_id=user.id)


##########################################################
# get_user_workspaces_overview
##########################################################


async def test_get_my_workspaces_projects():
    user = await f.create_user()

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
    ws_id = uuid.uuid1()
    with patch(
        "workspaces.workspaces.services.workspaces_repositories", autospec=True
    ) as fake_workspaces_repo:
        await services.get_workspace(id=ws_id)
        fake_workspaces_repo.get_workspace.assert_awaited_with(filters={"id": ws_id})


##########################################################
# get_workspace_detail
##########################################################


async def test_get_workspace_detail():
    workspace = await f.create_workspace(name="test")
    workspace.has_projects = True

    with (
        patch(
            "workspaces.workspaces.services.workspaces_repositories", autospec=True
        ) as fake_workspaces_repo,
        patch(
            "workspaces.workspaces.services.projects_repositories", autospec=True
        ) as fake_projects_repo,
    ):
        fake_projects_repo.get_total_projects.return_value = 1
        fake_workspaces_repo.get_workspace_detail.return_value = workspace
        await services.get_workspace_detail(
            id=workspace.id, user_id=workspace.created_by.id
        )
        fake_workspaces_repo.get_workspace_detail.assert_awaited_with(
            user_id=workspace.created_by.id,
            filters={"id": workspace.id},
        )


##########################################################
# get_workspace_nested
##########################################################


async def get_workspace_nested():
    workspace = await f.create_workspace()

    with (
        patch(
            "workspaces.workspaces.services.workspaces_repositories", autospec=True
        ) as fake_workspaces_repo,
        patch(
            "workspaces.workspaces.services.ws_roles_services", autospec=True
        ) as fake_ws_roles_services,
    ):
        fake_ws_roles_services.get_workspace_role_name.return_value = "admin"
        fake_workspaces_repo.get_workspace_summary.return_value = workspace

        await services.get_workspace_summary(
            id=workspace.id, user_id=workspace.created_by.id
        )

        fake_ws_roles_services.get_workspace_role_name.assert_awaited_with(
            workspace_id=workspace.id, user_id=workspace.created_by.id
        )
        fake_workspaces_repo.get_workspace_summary.assert_awaited_with(
            filters={"id": workspace.id},
        )


##########################################################
# update_workspace
##########################################################


async def test_update_workspace_ok(tqmanager):
    workspace = f.build_workspace()
    values = {"name": "new name"}

    with patch(
        "workspaces.workspaces.services.workspaces_repositories", autospec=True
    ) as fake_workspaces_repo:
        await services._update_workspace(workspace=workspace, values=values)
        fake_workspaces_repo.update_workspace.assert_awaited_once_with(
            workspace=workspace, values=values
        )
        assert len(tqmanager.pending_jobs) == 0


##########################################################
# delete_workspace
##########################################################


async def test_delete_workspace_without_projects():
    workspace = await f.create_workspace()

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
        fake_workspaces_repo.delete_workspaces.return_value = 4

        ret = await services.delete_workspace(
            workspace=workspace, deleted_by=workspace.created_by
        )

        fake_projects_repo.get_total_projects.assert_awaited_with(
            filters={"workspace_id": workspace.id}
        )
        fake_workspaces_repo.delete_workspaces.assert_awaited_with(
            filters={"id": workspace.id}
        )
        fake_workspaces_events.emit_event_when_workspace_is_deleted.assert_awaited()
        assert ret is True


async def test_delete_workspace_with_projects():
    workspace = await f.create_workspace()

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

        fake_workspaces_repo.delete_workspaces.assert_not_awaited()
        fake_workspaces_events.emit_event_when_workspace_is_deleted.assert_not_awaited()


async def test_delete_workspace_not_deleted_in_db():
    workspace = await f.create_workspace()

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
        fake_workspaces_repo.delete_workspaces.return_value = 0
        ret = await services.delete_workspace(
            workspace=workspace, deleted_by=workspace.created_by
        )

        fake_projects_repo.get_total_projects.assert_awaited_with(
            filters={"workspace_id": workspace.id}
        )
        fake_workspaces_repo.delete_workspaces.assert_awaited_with(
            filters={"id": workspace.id}
        )
        fake_workspaces_events.emit_event_when_workspace_is_deleted.assert_not_awaited()

        assert ret is False

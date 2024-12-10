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

from projects.roles import services
from projects.roles.services import exceptions as ex
from tests.utils import factories as f

#######################################################
# list_project_roles_as_dict
#######################################################


async def test_list_project_roles_as_dict():
    role = f.build_project_role(is_admin=True)

    with patch(
        "projects.roles.services.pj_roles_repositories", autospec=True
    ) as fake_role_repository:
        fake_role_repository.list_project_roles.return_value = [role]
        ret = await services.list_project_roles_as_dict(project=role.project)

        fake_role_repository.list_project_roles.assert_awaited_once_with(
            filters={"project_id": role.project_id}
        )
        assert ret[role.slug] == role


#######################################################
# get_project_role
#######################################################


async def test_get_project_role():
    project = f.build_project()
    slug = "general"

    with patch(
        "projects.roles.services.pj_roles_repositories", autospec=True
    ) as fake_role_repository:
        fake_role_repository.get_project_role.return_value = f.build_project_role()
        await services.get_project_role(project_id=project.id, slug=slug)
        fake_role_repository.get_project_role.assert_awaited_once()


#######################################################
# update_project_role
#######################################################


async def test_update_project_role_permissions_is_admin():
    role = f.build_project_role(is_admin=True)
    permissions = []

    with (
        patch(
            "projects.roles.services.pj_roles_events", autospec=True
        ) as fake_roles_events,
        pytest.raises(ex.NonEditableRoleError),
    ):
        await services.update_project_role_permissions(
            role=role, permissions=permissions
        )
        fake_roles_events.emit_event_when_project_role_permissions_are_updated.assert_not_awaited()


async def test_update_project_role_permissions_ok():
    role = f.build_project_role()
    permissions = ["view_story"]

    with (
        patch(
            "projects.roles.services.pj_roles_events", autospec=True
        ) as fake_roles_events,
        patch(
            "projects.roles.services.pj_roles_repositories", autospec=True
        ) as fake_role_repository,
    ):
        fake_role_repository.update_project_role_permissions.return_value = role
        await services.update_project_role_permissions(
            role=role, permissions=permissions
        )
        fake_role_repository.update_project_role_permissions.assert_awaited_once()
        fake_roles_events.emit_event_when_project_role_permissions_are_updated.assert_awaited_with(
            role=role
        )


async def test_update_project_role_permissions_view_story_deleted():
    role = f.build_project_role()
    permissions = []
    user = f.build_user()
    f.build_project_membership(user=user, project=role.project, role=role)
    story = f.build_story(project=role.project)
    f.build_story_assignment(story=story, user=user)

    with (
        patch(
            "projects.roles.services.pj_roles_events", autospec=True
        ) as fake_roles_events,
        patch(
            "projects.roles.services.pj_roles_repositories", autospec=True
        ) as fake_role_repository,
        patch(
            "projects.roles.services.permissions_services", autospec=True
        ) as fake_permissions_service,
        patch(
            "projects.roles.services.story_assignments_repositories", autospec=True
        ) as fake_story_assignments_repository,
    ):
        fake_role_repository.update_project_role_permissions.return_value = role
        fake_permissions_service.is_view_story_permission_deleted.return_value = True
        await services.update_project_role_permissions(
            role=role, permissions=permissions
        )
        fake_role_repository.update_project_role_permissions.assert_awaited_once()
        fake_roles_events.emit_event_when_project_role_permissions_are_updated.assert_awaited_with(
            role=role
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_awaited_once_with(
            filters={"role_id": role.id}
        )

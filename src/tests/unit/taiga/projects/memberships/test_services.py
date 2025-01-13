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

from projects.memberships import services
from projects.memberships.services import exceptions as ex
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


#######################################################
# list_paginated_project_memberships
#######################################################


async def test_list_project_memberships():
    project = f.build_project()
    with patch(
        "projects.memberships.services.memberships_repositories", autospec=True
    ) as fake_membership_repository:
        await services.list_project_memberships(project=project)
        fake_membership_repository.list_project_memberships.assert_awaited_once()


#######################################################
# update_project_membership
#######################################################


async def test_update_project_membership_role_non_existing_role():
    project = f.build_project()
    user = f.build_user()
    general_role = f.build_project_role(project=project, is_admin=False)
    membership = f.build_project_membership(
        user=user, project=project, role=general_role
    )
    non_existing_role_slug = "non_existing_role_slug"
    with (
        patch(
            "projects.memberships.services.pj_roles_repositories", autospec=True
        ) as fake_pj_role_repository,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        pytest.raises(ex.NonExistingRoleError),
    ):
        fake_pj_role_repository.get_project_role.return_value = None

        await services.update_project_membership(
            membership=membership, role_slug=non_existing_role_slug
        )
        fake_pj_role_repository.get_project_role.assert_awaited_once_with(
            project=project, slug=non_existing_role_slug
        )
        fake_membership_repository.update_project_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_not_awaited()


async def test_update_project_membership_role_only_one_admin():
    project = f.build_project()
    admin_role = f.build_project_role(project=project, is_admin=True)
    membership = f.build_project_membership(
        user=project.created_by, project=project, role=admin_role
    )
    general_role = f.build_project_role(project=project, is_admin=False)
    with (
        patch(
            "projects.memberships.services.pj_roles_repositories", autospec=True
        ) as fake_pj_role_repository,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        pytest.raises(ex.MembershipIsTheOnlyAdminError),
    ):
        fake_pj_role_repository.get_project_role.return_value = general_role
        fake_membership_repository.get_total_project_memberships.return_value = 1

        await services.update_project_membership(
            membership=membership, role_slug=general_role.slug
        )
        fake_pj_role_repository.get_project_role.assert_awaited_once_with(
            filters={"project_id": project.id, "slug": general_role.slug}
        )
        fake_membership_repository.get_total_project_memberships.assert_awaited_once_with(
            filters={"role_id": admin_role.id}
        )
        fake_membership_repository.update_project_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_not_awaited()


async def test_update_project_membership_role_ok():
    project = f.build_project()
    user = f.build_user()
    general_role = f.build_project_role(project=project, is_admin=False)
    membership = f.build_project_membership(
        user=user, project=project, role=general_role
    )
    admin_role = f.build_project_role(project=project, is_admin=True)
    with (
        patch(
            "projects.memberships.services.pj_roles_repositories", autospec=True
        ) as fake_pj_role_repository,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
    ):
        fake_pj_role_repository.get_project_role.return_value = admin_role

        updated_membership = await services.update_project_membership(
            membership=membership, role_slug=admin_role.slug
        )
        fake_pj_role_repository.get_project_role.assert_awaited_once_with(
            filters={"project_id": project.id, "slug": admin_role.slug}
        )
        fake_membership_repository.get_total_project_memberships.assert_not_awaited()
        fake_membership_repository.update_project_membership.assert_awaited_once_with(
            membership=membership, values={"role": admin_role}
        )
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_awaited_once_with(
            membership=updated_membership
        )


async def test_update_project_membership_role_view_story_deleted():
    project = f.build_project()
    user = f.build_user()
    permissions = []
    admin_role = f.build_project_role(project=project, is_admin=True)
    role = f.build_project_role(
        project=project, is_admin=False, permissions=permissions
    )
    membership = f.build_project_membership(user=user, project=project, role=admin_role)
    with (
        patch(
            "projects.memberships.services.pj_roles_repositories", autospec=True
        ) as fake_pj_role_repository,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch(
            "projects.memberships.services.permissions_services", autospec=True
        ) as fake_permissions_service,
        patch(
            "projects.memberships.services.story_assignments_repositories",
            autospec=True,
        ) as fake_story_assignments_repository,
    ):
        fake_pj_role_repository.get_project_role.return_value = role
        fake_permissions_service.is_view_story_permission_deleted.return_value = True

        updated_membership = await services.update_project_membership(
            membership=membership, role_slug=role.slug
        )
        fake_pj_role_repository.get_project_role.assert_awaited_once_with(
            filters={"project_id": project.id, "slug": role.slug}
        )
        fake_membership_repository.update_project_membership.assert_awaited_once_with(
            membership=membership, values={"role": role}
        )
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_awaited_once_with(
            membership=updated_membership
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_awaited_once_with(
            filters={"project_id": project.id, "username": user.username}
        )


#######################################################
# delete_project_membership
#######################################################


async def test_delete_project_membership_only_one_admin():
    project = f.build_project()
    admin_role = f.build_project_role(project=project, is_admin=True)
    membership = f.build_project_membership(
        user=project.created_by, project=project, role=admin_role
    )
    with (
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        pytest.raises(ex.MembershipIsTheOnlyAdminError),
    ):
        fake_membership_repository.get_total_project_memberships.return_value = 1

        await services.delete_project_membership(membership=membership)
        fake_membership_repository.get_total_project_memberships.assert_awaited_once_with(
            filters={"role_id": admin_role.id}
        )
        fake_membership_repository.delete_project_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_deleted.assert_not_awaited()


async def test_delete_project_membership_ok():
    project = f.build_project()
    user = f.build_user()
    general_role = f.build_project_role(project=project, is_admin=False)
    membership = f.build_project_membership(
        user=user, project=project, role=general_role
    )
    with (
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.story_assignments_repositories",
            autospec=True,
        ) as fake_story_assignments_repository,
        patch(
            "projects.memberships.services.project_invitations_repositories",
            autospec=True,
        ) as fake_project_invitations_repository,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
    ):
        fake_membership_repository.delete_project_membership.return_value = 1
        await services.delete_project_membership(membership=membership)
        fake_membership_repository.delete_project_membership.assert_awaited_once_with(
            filters={"id": membership.id},
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_awaited_once_with(
            filters={
                "project_id": membership.project_id,
                "username": membership.user.username,
            }
        )
        fake_project_invitations_repository.delete_project_invitation.assert_awaited_once_with(
            filters={
                "project_id": membership.project_id,
                "username_or_email": membership.user.email,
            }
        )
        fake_membership_events.emit_event_when_project_membership_is_deleted.assert_awaited_once_with(
            membership=membership
        )

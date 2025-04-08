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
from permissions.choices import ProjectPermissions
from projects.invitations.models import ProjectInvitation
from projects.memberships import services
from projects.memberships.models import ProjectMembership, ProjectRole
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_SLUG
from tests.utils.utils import patch_db_transaction

#######################################################
# list_project_memberships
#######################################################


async def test_list_project_memberships():
    project = f.build_project()
    with patch(
        "projects.memberships.services.memberships_repositories", autospec=True
    ) as fake_membership_repository:
        await services.list_project_memberships(project=project)
        fake_membership_repository.list_memberships.assert_awaited_once()
        assert {
            "project_id": project.id
        } == fake_membership_repository.list_memberships.call_args.kwargs["filters"]


#######################################################
# get_project_membership
#######################################################


async def test_get_project_membership():
    project = f.build_project()
    with patch(
        "projects.memberships.services.memberships_repositories", autospec=True
    ) as fake_membership_repository:
        await services.get_project_membership(
            project_id=project.id, username=project.created_by.username
        )
        fake_membership_repository.get_membership.assert_awaited_once()
        assert {
            "project_id": project.id,
            "user__username": project.created_by.username,
        } == fake_membership_repository.get_membership.call_args.kwargs["filters"]


#######################################################
# update_project_membership
#######################################################


async def test_update_project_membership_role_non_existing_role():
    project = f.build_project()
    user = f.build_user()
    member_role = f.build_project_role(project=project, is_owner=False)
    membership = f.build_project_membership(
        user=user, project=project, role=member_role
    )
    with (
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
        pytest.raises(ex.NonExistingRoleError),
    ):
        fake_membership_repository.get_role.side_effect = ProjectRole.DoesNotExist

        await services.update_project_membership(
            membership=membership, role_slug=NOT_EXISTING_SLUG
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            ProjectRole,
            filters={"project_id": project.id, "slug": NOT_EXISTING_SLUG},
        )
        fake_membership_repository.update_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_not_awaited()


async def test_update_project_membership_role_only_one_owner():
    project = f.build_project()
    owner_role = f.build_project_role(project=project, is_owner=True)
    membership = f.build_project_membership(
        user=project.created_by, project=project, role=owner_role
    )
    general_role = f.build_project_role(project=project, is_owner=False)
    with (
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
        pytest.raises(ex.MembershipIsTheOnlyOwnerError),
    ):
        fake_membership_repository.get_role.return_value = general_role
        fake_membership_service.is_membership_the_only_owner.return_value = True

        await services.update_project_membership(
            membership=membership, role_slug=general_role.slug
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            ProjectRole, filters={"project_id": project.id, "slug": general_role.slug}
        )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_membership_repository.update_project_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_not_awaited()


async def test_update_project_membership_role_ok():
    project = f.build_project()
    user = f.build_user()
    general_role = f.build_project_role(project=project, is_owner=False)
    membership = f.build_project_membership(
        user=user, project=project, role=general_role
    )
    owner_role = f.build_project_role(project=project, is_owner=True)
    with (
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch(
            "projects.memberships.services.story_assignments_repositories",
            autospec=True,
        ) as fake_story_assignments_repository,
        patch_db_transaction(),
    ):
        fake_membership_repository.get_role.return_value = owner_role

        updated_membership = await services.update_project_membership(
            membership=membership, role_slug=owner_role.slug
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            ProjectRole, filters={"project_id": project.id, "slug": owner_role.slug}
        )
        fake_membership_service.is_membership_the_only_owner.assert_not_awaited()
        fake_membership_repository.update_membership.assert_awaited_once_with(
            membership=membership, values={"role": owner_role}
        )
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_awaited_once_with(
            membership=updated_membership
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_not_awaited()


async def test_update_project_membership_role_view_story_deleted():
    project = f.build_project()
    user = f.build_user()
    permissions = []
    owner_role = f.build_project_role(project=project, is_owner=True)
    role = f.build_project_role(
        project=project, is_owner=False, permissions=permissions
    )
    membership = f.build_project_membership(user=user, project=project, role=owner_role)
    with (
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch(
            "projects.memberships.services.story_assignments_repositories",
            autospec=True,
        ) as fake_story_assignments_repository,
        patch_db_transaction(),
    ):
        fake_membership_repository.get_role.return_value = role
        fake_membership_service.is_membership_the_only_owner.return_value = False

        updated_membership = await services.update_project_membership(
            membership=membership, role_slug=role.slug
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            ProjectRole, filters={"project_id": project.id, "slug": role.slug}
        )
        fake_membership_repository.update_membership.assert_awaited_once_with(
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


async def test_delete_project_membership_only_one_owner():
    project = f.build_project()
    owner_role = f.build_project_role(project=project, is_owner=True)
    membership = f.build_project_membership(
        user=project.created_by, project=project, role=owner_role
    )
    with (
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        pytest.raises(ex.MembershipIsTheOnlyOwnerError),
    ):
        fake_membership_service.is_membership_the_only_owner.return_value = True

        await services.delete_project_membership(membership=membership)
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_membership_repository.delete_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_deleted.assert_not_awaited()


async def test_delete_project_membership_ok():
    project = f.build_project()
    user = f.build_user()
    general_role = f.build_project_role(project=project, is_owner=False)
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
        fake_membership_repository.delete_membership.return_value = 1
        fake_project_invitations_repository.username_or_email_query.return_value = None
        await services.delete_project_membership(membership=membership)
        fake_membership_repository.delete_membership.assert_awaited_once_with(
            membership
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_awaited_once_with(
            filters={
                "project_id": project.id,
                "username": membership.user.username,
            }
        )
        fake_project_invitations_repository.delete_invitation.assert_awaited_once_with(
            ProjectInvitation,
            filters={
                "project_id": project.id,
            },
            q_filter=None,
        )
        fake_membership_events.emit_event_when_project_membership_is_deleted.assert_awaited_once_with(
            membership=membership
        )


#######################################################
# misc is_membership_the_only_owner
#######################################################


async def test_is_project_membership_the_only_owner_not_owner_role():
    role = f.build_project_role(is_owner=False)
    membership = f.build_project_membership(role=role)
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
    ):
        assert not await services.is_membership_the_only_owner(membership)
        fake_membership_repository.has_other_owner_memberships.assert_not_called()


async def test_is_project_membership_the_only_owner_true():
    role = f.build_project_role(is_owner=True)
    membership = f.build_project_membership(role=role)
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
    ):
        fake_membership_repository.has_other_owner_memberships.return_value = False
        assert await services.is_membership_the_only_owner(membership)
        fake_membership_repository.has_other_owner_memberships.assert_awaited_once_with(
            membership=membership
        )


async def test_is_project_membership_the_only_owner_false():
    role = f.build_project_role(is_owner=True)
    membership = f.build_project_membership(role=role)
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
    ):
        fake_membership_repository.has_other_owner_memberships.return_value = True
        assert not await services.is_membership_the_only_owner(membership)
        fake_membership_repository.has_other_owner_memberships.assert_awaited_once_with(
            membership=membership
        )


#######################################################
# misc has_permission
#######################################################


async def test_has_project_permission_ok():
    project = f.build_project()
    user = f.build_user()
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
    ):
        fake_membership_repository.get_user_permissions.return_value = (
            ProjectPermissions.values
        )
        assert await services.has_permission(
            user, project, ProjectPermissions.VIEW_STORY
        )
        fake_membership_repository.get_user_permissions.assert_awaited_once_with(
            user, project
        )


async def test_has_project_permission_forbidden():
    project = f.build_project()
    user = f.build_user()
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
    ):
        fake_membership_repository.get_user_permissions.return_value = [
            ProjectPermissions.VIEW_STORY.value,
            ProjectPermissions.CREATE_MODIFY_MEMBER.value,
        ]
        assert not await services.has_permission(
            user, project, ProjectPermissions.CREATE_STORY
        )
        fake_membership_repository.get_user_permissions.assert_awaited_once_with(
            user, project
        )


async def test_has_project_permission_not_a_member():
    project = f.build_project()
    user = f.build_user()
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
    ):
        fake_membership_repository.get_user_permissions.side_effect = (
            ProjectMembership.DoesNotExist
        )
        assert not await services.has_permission(
            user, project, ProjectPermissions.VIEW_STORY
        )
        fake_membership_repository.get_user_permissions.assert_awaited_once_with(
            user, project
        )


##########################################################
# list_project_role
##########################################################


async def test_list_project_role():
    project = f.build_project()
    role = f.build_project_role(project=project)
    with (
        patch(
            "projects.memberships.services.memberships_repositories",
            autospec=True,
        ) as fake_ws_memberships_repo,
    ):
        fake_ws_memberships_repo.list_roles.return_value = [role]
        ret = await services.list_project_roles(project)

        fake_ws_memberships_repo.list_roles.assert_awaited_once_with(
            ProjectRole, filters={"project_id": project.id}
        )
        assert ret == [role]


#######################################################
# get_project_role
#######################################################


async def test_get_project_role():
    project = f.build_project()
    role = f.build_project_role(project=project)
    with (
        patch(
            "projects.memberships.services.memberships_repositories",
            autospec=True,
        ) as fake_ws_memberships_repo,
    ):
        fake_ws_memberships_repo.get_role.return_value = role
        ret = await services.get_project_role(project_id=project.id, slug=role.slug)

        fake_ws_memberships_repo.get_role.assert_awaited_once_with(
            ProjectRole,
            filters={"project_id": project.id, "slug": role.slug},
            select_related=["project"],
        )
        assert ret == role


#######################################################
# update_project_role
#######################################################


async def test_update_project_role_permissions_is_owner():
    role = f.build_project_role(editable=False)
    permissions = []

    with (
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch_db_transaction(),
        pytest.raises(ex.NonEditableRoleError),
    ):
        await services.update_project_role_permissions(
            role=role, permissions=permissions
        )
        fake_memberships_repositories.update_role.assert_not_awaited()


async def test_update_project_role_permissions_ok():
    role = f.build_project_role()
    permissions = [ProjectPermissions.VIEW_STORY.value]

    with (
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch_db_transaction(),
    ):
        fake_memberships_repositories.update_role.return_value = role
        await services.update_project_role_permissions(
            role=role, permissions=permissions
        )
        fake_memberships_repositories.update_role.assert_awaited_once_with(
            role=role,
            values={"permissions": permissions},
        )
        fake_memberships_events.emit_event_when_project_role_permissions_are_updated.assert_awaited_with(
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
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.memberships.services.story_assignments_repositories",
            autospec=True,
        ) as fake_story_assignments_repository,
        patch_db_transaction(),
    ):
        fake_memberships_repositories.update_role.return_value = role
        await services.update_project_role_permissions(
            role=role, permissions=permissions
        )
        fake_memberships_repositories.update_role.assert_awaited_once_with(
            role=role,
            values={"permissions": permissions},
        )
        fake_memberships_events.emit_event_when_project_role_permissions_are_updated.assert_awaited_with(
            role=role
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_awaited_once_with(
            filters={"role_id": role.id}
        )

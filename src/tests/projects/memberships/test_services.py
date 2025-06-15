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
from django.db.models import RestrictedError

from memberships.services import exceptions as ex
from permissions.choices import ProjectPermissions
from projects.invitations.models import ProjectInvitation
from projects.memberships import services
from projects.memberships.models import ProjectMembership, ProjectRole
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID
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
    membership = f.build_project_membership()
    with patch(
        "projects.memberships.services.memberships_repositories", autospec=True
    ) as fake_membership_repository:
        await services.get_project_membership(
            membership_id=membership.id,
        )
        fake_membership_repository.get_membership.assert_awaited_once()
        assert {
            "id": membership.id,
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
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
        pytest.raises(ex.NonExistingRoleError),
    ):
        fake_membership_repository.get_role.side_effect = ProjectRole.DoesNotExist

        await services.update_project_membership(
            membership=membership, role_id=NOT_EXISTING_UUID, user=f.build_user()
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            ProjectRole,
            filters={"project_id": project.id, "id": NOT_EXISTING_UUID},
        )
        fake_membership_repository.update_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_not_awaited()


async def test_update_project_membership_role_only_one_owner():
    project = f.build_project()
    role = f.build_project_role(project=project, is_owner=False)
    membership = f.build_project_membership(
        user=project.created_by, project=project, role=role
    )
    other_role = f.build_project_role(project=project, is_owner=False)
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "memberships.services.is_membership_the_only_owner", autospec=True
        ) as fake_is_membership_the_only_owner,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
        pytest.raises(ex.MembershipIsTheOnlyOwnerError),
    ):
        fake_membership_repository.get_role.return_value = other_role
        fake_is_membership_the_only_owner.return_value = True

        await services.update_project_membership(
            membership=membership, role_id=other_role.id, user=f.build_user()
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            ProjectRole, filters={"project_id": project.id, "id": other_role.id}
        )
        fake_is_membership_the_only_owner.assert_awaited_once_with(membership)
        fake_membership_repository.update_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_not_awaited()


async def test_update_project_membership_role_owner():
    project = f.build_project()
    owner_role = f.build_project_role(project=project, is_owner=True)
    general_role = f.build_project_role(project=project, is_owner=False)
    membership = f.build_project_membership(
        user=project.created_by, project=project, role=general_role
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
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
        updated_membership = f.build_project_membership(
            user=project.created_by, project=project, role=owner_role
        )
        fake_membership_repository.update_membership.return_value = updated_membership
        with pytest.raises(ex.OwnerRoleNotAuthorisedError):
            await services.update_project_membership(
                membership=membership, role_id=owner_role.id, user=f.build_user()
            )
        fake_membership_repository.get_role.assert_awaited_once_with(
            ProjectRole, filters={"project_id": project.id, "id": owner_role.id}
        )
        fake_membership_repository.update_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_not_awaited()
        fake_story_assignments_repository.delete_stories_assignments.assert_not_awaited()

        owner_user = f.build_user()
        owner_user.project_role = owner_role
        updated_membership = await services.update_project_membership(
            membership=membership, role_id=owner_role.id, user=owner_user
        )
        fake_membership_repository.update_membership.assert_awaited_once_with(
            membership=membership, values={"role": owner_role}
        )
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_awaited_once_with(
            membership=updated_membership
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_not_awaited()


async def test_update_project_membership_role_ok():
    project = f.build_project()
    user = f.build_user()
    general_role = f.build_project_role(project=project, is_owner=False)
    membership = f.build_project_membership(
        user=user, project=project, role=general_role
    )
    other_role = f.build_project_role(project=project, is_owner=False)
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "memberships.services.is_membership_the_only_owner", autospec=True
        ) as fake_is_membership_the_only_owner,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch(
            "projects.memberships.services.story_assignments_repositories",
            autospec=True,
        ) as fake_story_assignments_repository,
        patch_db_transaction(),
    ):
        fake_membership_repository.get_role.return_value = other_role
        fake_is_membership_the_only_owner.return_value = False
        updated_membership = f.build_project_membership(
            user=user, project=project, role=other_role
        )
        fake_membership_repository.update_membership.return_value = updated_membership

        updated_membership = await services.update_project_membership(
            membership=membership, role_id=other_role.id, user=f.build_user()
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            ProjectRole, filters={"project_id": project.id, "id": other_role.id}
        )
        fake_is_membership_the_only_owner.assert_awaited_once_with(membership)
        fake_membership_repository.update_membership.assert_awaited_once_with(
            membership=membership, values={"role": other_role}
        )
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_awaited_once_with(
            membership=updated_membership
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_not_awaited()


async def test_update_project_membership_role_view_story_deleted():
    project = f.build_project()
    user = f.build_user()
    permissions = []
    role = f.build_project_role(project=project, is_owner=False)
    other_role = f.build_project_role(
        project=project, is_owner=False, permissions=permissions
    )
    membership = f.build_project_membership(user=user, project=project, role=role)
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "memberships.services.is_membership_the_only_owner", autospec=True
        ) as fake_is_membership_the_only_owner,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch(
            "projects.memberships.services.story_assignments_repositories",
            autospec=True,
        ) as fake_story_assignments_repository,
        patch_db_transaction(),
    ):
        fake_membership_repository.get_role.return_value = other_role
        fake_is_membership_the_only_owner.return_value = False
        updated_membership = f.build_project_membership(
            user=user, project=project, role=other_role
        )
        fake_membership_repository.update_membership.return_value = updated_membership

        updated_membership = await services.update_project_membership(
            membership=membership, role_id=other_role.id, user=f.build_user()
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            ProjectRole, filters={"project_id": project.id, "id": other_role.id}
        )
        fake_membership_repository.update_membership.assert_awaited_once_with(
            membership=membership, values={"role": other_role}
        )
        fake_membership_events.emit_event_when_project_membership_is_updated.assert_awaited_once_with(
            membership=updated_membership
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_awaited_once_with(
            filters={"story__project_id": project.id, "user_id": user.id}
        )


#######################################################
# delete_project_membership
#######################################################


async def test_delete_project_membership_only_one_owner_without_successor():
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
        patch_db_transaction(),
        pytest.raises(ex.MembershipIsTheOnlyOwnerError),
    ):
        fake_membership_service.is_membership_the_only_owner.return_value = True

        await services.delete_project_membership(
            membership=membership, user=membership.user
        )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_membership_repository.delete_memberships.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_deleted.assert_not_awaited()


async def test_delete_project_membership_only_one_owner_bad_successor():
    project = f.build_project()
    owner_role = f.build_project_role(project=project, is_owner=False)
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
        patch(
            "projects.memberships.services.update_project_membership", autospec=True
        ) as fake_update_project_membership,
        patch_db_transaction(),
    ):
        fake_membership_service.is_membership_the_only_owner.return_value = True
        # same successor as deleted member
        with pytest.raises(ex.SameSuccessorAsCurrentMember):
            await services.delete_project_membership(
                membership=membership,
                user=membership.user,
                successor_user_id=membership.user.id,
            )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_update_project_membership.assert_not_awaited()
        fake_membership_repository.delete_memberships.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_deleted.assert_not_awaited()

        fake_membership_service.is_membership_the_only_owner.reset_mock()
        fake_membership_repository.get_membership.side_effect = (
            ProjectMembership.DoesNotExist
        )
        # successor is not found
        with pytest.raises(ex.MembershipIsTheOnlyOwnerError):
            await services.delete_project_membership(
                membership=membership,
                user=membership.user,
                successor_user_id=NOT_EXISTING_UUID,
            )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_membership_repository.get_membership.assert_awaited_once_with(
            ProjectMembership,
            filters={
                "user_id": NOT_EXISTING_UUID,
                "project_id": project.id,
            },
            select_related=["user"],
        )
        fake_update_project_membership.assert_not_awaited()
        fake_membership_repository.delete_memberships.assert_not_awaited()
        fake_membership_events.emit_event_when_project_membership_is_deleted.assert_not_awaited()


async def test_delete_project_membership_only_one_owner_successor_ok():
    project = f.build_project()
    owner_role = f.build_project_role(project=project, is_owner=False)
    membership = f.build_project_membership(
        user=project.created_by, project=project, role=owner_role
    )
    successor = f.build_user()
    successor_membership = f.build_project_membership(user=successor, project=project)
    with (
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "projects.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
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
        patch(
            "projects.memberships.services.update_project_membership", autospec=True
        ) as fake_update_project_membership,
        patch_db_transaction(),
    ):
        fake_membership_repository.delete_memberships.return_value = 1
        fake_project_invitations_repository.invitation_username_or_email_query.return_value = None
        fake_membership_service.is_membership_the_only_owner.return_value = True
        fake_membership_repository.get_membership.return_value = successor_membership

        await services.delete_project_membership(
            membership=membership, user=membership.user, successor_user_id=successor.id
        )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_update_project_membership.assert_awaited_once_with(
            successor_membership, owner_role.id, user=membership.user
        )
        fake_membership_repository.delete_memberships.assert_awaited_once_with(
            ProjectMembership, {"id": membership.id}
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_awaited_once_with(
            filters={
                "story__project_id": project.id,
                "user_id": membership.user_id,
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
            membership=membership, workspace_id=project.workspace_id
        )


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
        patch_db_transaction(),
    ):
        fake_membership_repository.delete_memberships.return_value = 1
        fake_project_invitations_repository.invitation_username_or_email_query.return_value = None
        await services.delete_project_membership(
            membership=membership, user=membership.user
        )
        fake_membership_repository.delete_memberships.assert_awaited_once_with(
            ProjectMembership, {"id": membership.id}
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_awaited_once_with(
            filters={
                "story__project_id": project.id,
                "user_id": membership.user_id,
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
            membership=membership, workspace_id=project.workspace_id
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
            ProjectRole, filters={"project_id": project.id}, get_members_details=True
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
        ret = await services.get_project_role(role_id=role.id)

        fake_ws_memberships_repo.get_role.assert_awaited_once_with(
            ProjectRole,
            filters={"id": role.id},
            select_related=["project"],
            get_members_details=False,
        )
        assert ret == role


#######################################################
# update_project_role
#######################################################


async def test_create_project_role():
    project = f.build_project()
    permissions = []
    name = "Dev"

    with (
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch_db_transaction(),
    ):
        await services.create_project_role(
            name=name,
            permissions=permissions,
            project_id=project.id,
        )
        fake_memberships_repositories.create_project_role.assert_awaited_once_with(
            name=name,
            permissions=permissions,
            project_id=project.id,
        )
        fake_memberships_events.emit_event_when_project_role_is_created.assert_awaited_once_with(
            fake_memberships_repositories.create_project_role.return_value
        )


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
        await services.update_project_role(
            role=role, values={"permissions": permissions}
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
        await services.update_project_role(
            role=role, values={"permissions": permissions}
        )
        fake_memberships_repositories.update_role.assert_awaited_once_with(
            role=role,
            values={"permissions": permissions},
        )
        fake_memberships_events.emit_event_when_project_role_is_updated.assert_awaited_with(
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
        await services.update_project_role(
            role=role, values={"permissions": permissions}
        )
        fake_memberships_repositories.update_role.assert_awaited_once_with(
            role=role,
            values={"permissions": permissions},
        )
        fake_memberships_events.emit_event_when_project_role_is_updated.assert_awaited_with(
            role=role
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_awaited_once_with(
            filters={"user__project_memberships__role_id": role.id}
        )


async def test_update_project_role_name():
    role = f.build_project_role()
    user = f.build_user()
    f.build_project_membership(user=user, project=role.project, role=role)
    story = f.build_story(project=role.project)
    f.build_story_assignment(story=story, user=user)
    new_name = "New member"

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
        await services.update_project_role(role=role, values={"name": new_name})
        fake_memberships_repositories.update_role.assert_awaited_once_with(
            role=role,
            values={"name": new_name},
        )
        fake_memberships_events.emit_event_when_project_role_is_updated.assert_awaited_with(
            role=role
        )
        fake_story_assignments_repository.delete_stories_assignments.assert_not_awaited()


#######################################################
# delete_project_role
#######################################################


async def test_delete_project_role_ok():
    role = f.build_project_role()
    user = f.build_user()

    with (
        patch(
            "projects.memberships.services.get_project_role", autospec=True
        ) as fake_get_project_role,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch_db_transaction(),
    ):
        fake_memberships_repositories.delete_project_role.return_value = 1
        await services.delete_project_role(role=role, user=user)
        fake_get_project_role.assert_not_awaited()
        fake_memberships_repositories.delete_project_role.assert_awaited_once_with(
            role=role,
        )
        fake_memberships_events.emit_event_when_project_role_is_deleted.assert_awaited_once_with(
            role=role, target_role=None
        )
        fake_memberships_repositories.move_project_role_of_related.assert_not_awaited()


async def test_delete_project_role_ok_with_move_to():
    role = f.build_project_role()
    target_role = f.build_project_role(project=role.project)
    user = f.build_user()
    user.project_role = role

    with (
        patch(
            "projects.memberships.services.get_project_role", autospec=True
        ) as fake_get_project_role,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch_db_transaction(),
    ):
        fake_get_project_role.return_value = target_role
        fake_memberships_repositories.delete_project_role.return_value = 1
        await services.delete_project_role(
            role=role, user=user, target_role_id=target_role.id
        )
        fake_get_project_role.assert_awaited_once_with(
            role_id=target_role.id,
        )
        fake_memberships_repositories.delete_project_role.assert_awaited_once_with(
            role=role,
        )
        fake_memberships_events.emit_event_when_project_role_is_deleted.assert_awaited_once_with(
            role=role, target_role=target_role
        )
        fake_memberships_repositories.move_project_role_of_related.assert_awaited_once_with(
            role=role, target_role=target_role
        )


async def test_delete_project_role_ko_non_editable():
    role = f.build_project_role(editable=False)
    user = f.build_user()

    with (
        patch(
            "projects.memberships.services.get_project_role", autospec=True
        ) as fake_get_project_role,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch_db_transaction(),
        pytest.raises(ex.NonEditableRoleError),
    ):
        await services.delete_project_role(role=role, user=user)
        fake_get_project_role.assert_not_awaited()
        fake_memberships_repositories.delete_project_role.assert_not_awaited()
        fake_memberships_events.emit_event_when_project_role_is_deleted.assert_not_awaited()
        fake_memberships_repositories.move_project_role_of_related.assert_not_awaited()


async def test_delete_project_role_ko_not_existing_target_role_id():
    role = f.build_project_role()
    user = f.build_user()

    with (
        patch(
            "projects.memberships.services.get_project_role", autospec=True
        ) as fake_get_project_role,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch_db_transaction(),
        pytest.raises(ex.NonExistingMoveToRole),
    ):
        fake_get_project_role.side_effect = ProjectRole.DoesNotExist
        target_role_id = NOT_EXISTING_UUID
        await services.delete_project_role(
            role=role, user=user, target_role_id=target_role_id
        )
        fake_get_project_role.assert_awaited_once_with(
            project_id=role.project_id,
            role_id=target_role_id,
        )
        fake_memberships_repositories.delete_project_role.assert_not_awaited()
        fake_memberships_events.emit_event_when_project_role_is_deleted.assert_not_awaited()
        fake_memberships_repositories.move_project_role_of_related.assert_not_awaited()


async def test_delete_project_role_ko_role_same_as_target():
    role = f.build_project_role()
    user = f.build_user()

    with (
        patch(
            "projects.memberships.services.get_project_role", autospec=True
        ) as fake_get_project_role,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch_db_transaction(),
        pytest.raises(ex.SameMoveToRole),
    ):
        fake_get_project_role.return_value = role
        await services.delete_project_role(role=role, user=user, target_role_id=role.id)
        fake_get_project_role.assert_awaited_once_with(
            project_id=role.project_id,
            id=role.id,
        )
        fake_memberships_repositories.delete_project_role.assert_not_awaited()
        fake_memberships_events.emit_event_when_project_role_is_deleted.assert_not_awaited()
        fake_memberships_repositories.move_project_role_of_related.assert_not_awaited()


async def test_delete_project_role_ko_target_role_different_project():
    role = f.build_project_role()
    target_role = f.build_project_role()
    user = f.build_user()

    with (
        patch(
            "projects.memberships.services.get_project_role", autospec=True
        ) as fake_get_project_role,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch_db_transaction(),
        pytest.raises(ex.NonExistingMoveToRole),
    ):
        fake_get_project_role.return_value = target_role
        await services.delete_project_role(
            role=role, user=user, target_role_id=target_role.id
        )
        fake_get_project_role.assert_awaited_once_with(
            project_id=role.project_id,
            id=target_role.id,
        )
        fake_memberships_repositories.delete_project_role.assert_not_awaited()
        fake_memberships_events.emit_event_when_project_role_is_deleted.assert_not_awaited()
        fake_memberships_repositories.move_project_role_of_related.assert_not_awaited()


async def test_delete_project_role_ko_target_owner():
    role = f.build_project_role()
    owner_role = f.build_project_role(is_owner=True, project=role.project)
    user = f.build_user()
    user.project_role = role

    with (
        patch(
            "projects.memberships.services.get_project_role", autospec=True
        ) as fake_get_project_role,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch_db_transaction(),
        pytest.raises(ex.OwnerRoleNotAuthorisedError),
    ):
        fake_get_project_role.return_value = owner_role
        await services.delete_project_role(
            role=role, user=user, target_role_id=owner_role.id
        )
        fake_get_project_role.assert_awaited_once_with(
            project_id=role.project_id,
            role_id=role.id,
        )
        fake_memberships_repositories.delete_project_role.assert_not_awaited()
        fake_memberships_events.emit_event_when_project_role_is_deleted.assert_not_awaited()
        fake_memberships_repositories.move_project_role_of_related.assert_not_awaited()


async def test_delete_project_role_ko_restricted_db():
    role = f.build_project_role()
    user = f.build_user()

    with (
        patch(
            "projects.memberships.services.get_project_role", autospec=True
        ) as fake_get_project_role,
        patch(
            "projects.memberships.services.memberships_repositories", autospec=True
        ) as fake_memberships_repositories,
        patch(
            "projects.memberships.services.memberships_events", autospec=True
        ) as fake_memberships_events,
        patch_db_transaction(),
        pytest.raises(ex.RequiredMoveToRole),
    ):
        fake_memberships_repositories.delete_project_role.side_effect = RestrictedError(
            "", set()
        )
        await services.delete_project_role(role=role, user=user)
        fake_get_project_role.assert_not_awaited()
        fake_memberships_repositories.delete_project_role.assert_awaited_once_with(
            role=role
        )
        fake_memberships_events.emit_event_when_project_role_is_deleted.assert_not_awaited()
        fake_memberships_repositories.move_project_role_of_related.assert_not_awaited()

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
from projects.memberships.models import ProjectMembership
from projects.projects.models import Project
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID
from tests.utils.utils import patch_db_transaction
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships import services
from workspaces.memberships.models import WorkspaceMembership, WorkspaceRole

#######################################################
# list_workspace_memberships
#######################################################


async def test_list_workspace_memberships():
    workspace = f.build_workspace()

    with (
        patch(
            "workspaces.memberships.services.memberships_repositories",
            autospec=True,
        ) as fake_ws_membership_repository,
    ):
        await services.list_workspace_memberships(workspace=workspace)
        fake_ws_membership_repository.list_memberships.assert_awaited_once()
        assert {
            "workspace_id": workspace.id
        } == fake_ws_membership_repository.list_memberships.call_args.kwargs["filters"]


#######################################################
# get workspace membership
#######################################################


async def test_get_workspace_membership():
    membership = f.build_workspace_membership()
    with patch(
        "workspaces.memberships.services.memberships_repositories", autospec=True
    ) as fake_membership_repository:
        await services.get_workspace_membership(membership_id=membership.id)
        fake_membership_repository.get_membership.assert_awaited_once()
        assert {
            "id": membership.id,
        } == fake_membership_repository.get_membership.call_args.kwargs["filters"]


#######################################################
# update workspace membership
#######################################################


async def test_update_workspace_membership_role_non_existing_role():
    workspace = f.build_workspace()
    user = f.build_user()
    general_role = f.build_workspace_role(workspace=workspace, is_owner=False)
    membership = f.build_workspace_membership(
        user=user, workspace=workspace, role=general_role
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        pytest.raises(ex.NonExistingRoleError),
    ):
        fake_membership_repository.get_role.side_effect = WorkspaceRole.DoesNotExist

        await services.update_workspace_membership(
            membership=membership, role_id=NOT_EXISTING_UUID, user=f.build_user()
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            WorkspaceRole,
            filters={"workspace_id": workspace.id, "id": NOT_EXISTING_UUID},
        )
        fake_membership_repository.update_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_workspace_membership_is_updated.assert_not_awaited()


async def test_update_workspace_membership_role_only_one_owner():
    workspace = f.build_workspace()
    role = f.build_workspace_role(workspace=workspace, is_owner=False)
    membership = f.build_workspace_membership(
        user=workspace.created_by, workspace=workspace, role=role
    )
    other_role = f.build_workspace_role(workspace=workspace, is_owner=False)
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "memberships.services.is_membership_the_only_owner", autospec=True
        ) as fake_is_membership_the_only_owner,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        pytest.raises(ex.MembershipIsTheOnlyOwnerError),
    ):
        fake_membership_repository.get_role.return_value = other_role
        fake_is_membership_the_only_owner.return_value = True

        await services.update_workspace_membership(
            membership=membership, role_id=other_role.id, user=f.build_user()
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            WorkspaceRole,
            filters={"workspace_id": workspace.id, "id": other_role.id},
        )
        fake_is_membership_the_only_owner.assert_awaited_once_with(membership)
        fake_membership_repository.update_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_workspace_membership_is_updated.assert_not_awaited()


async def test_update_workspace_membership_role_owner():
    workspace = f.build_workspace()
    owner_role = f.build_workspace_role(workspace=workspace, is_owner=True)
    general_role = f.build_workspace_role(workspace=workspace, is_owner=False)
    membership = f.build_workspace_membership(
        user=workspace.created_by, workspace=workspace, role=general_role
    )
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
    ):
        fake_membership_repository.get_role.return_value = owner_role
        updated_membership = f.build_workspace_membership(
            user=workspace.created_by, workspace=workspace, role=owner_role
        )
        fake_membership_repository.update_membership.return_value = updated_membership
        with pytest.raises(ex.OwnerRoleNotAuthorisedError):
            await services.update_workspace_membership(
                membership=membership, role_id=owner_role.id, user=f.build_user()
            )
        fake_membership_repository.get_role.assert_awaited_once_with(
            WorkspaceRole,
            filters={"workspace_id": workspace.id, "id": owner_role.id},
        )
        fake_membership_repository.update_membership.assert_not_awaited()
        fake_membership_events.emit_event_when_workspace_membership_is_updated.assert_not_awaited()

        owner_user = f.build_user()
        owner_user.workspace_role = owner_role
        updated_membership = await services.update_workspace_membership(
            membership=membership, role_id=owner_role.id, user=owner_user
        )
        fake_membership_repository.update_membership.assert_awaited_once_with(
            membership=membership, values={"role": owner_role}
        )
        fake_membership_events.emit_event_when_workspace_membership_is_updated.assert_awaited_once_with(
            membership=updated_membership
        )


async def test_update_workspace_membership_role_ok():
    workspace = f.build_workspace()
    user = f.build_user()
    general_role = f.build_workspace_role(workspace=workspace, is_owner=False)
    membership = f.build_workspace_membership(
        user=user, workspace=workspace, role=general_role
    )
    other_role = f.build_workspace_role(workspace=workspace, is_owner=False)
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "memberships.services.is_membership_the_only_owner", autospec=True
        ) as fake_is_membership_the_only_owner,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
    ):
        fake_membership_repository.get_role.return_value = other_role
        fake_is_membership_the_only_owner.return_value = False
        updated_membership = f.build_workspace_membership(
            user=user, workspace=workspace, role=other_role
        )
        fake_membership_repository.update_membership.return_value = updated_membership

        updated_membership = await services.update_workspace_membership(
            membership=membership, role_id=other_role.id, user=f.build_user()
        )
        fake_membership_repository.get_role.assert_awaited_once_with(
            WorkspaceRole,
            filters={"workspace_id": workspace.id, "id": other_role.id},
        )
        fake_is_membership_the_only_owner.assert_awaited_once_with(membership)
        fake_membership_repository.update_membership.assert_awaited_once_with(
            membership=membership, values={"role": other_role}
        )
        fake_membership_events.emit_event_when_workspace_membership_is_updated.assert_awaited_once_with(
            membership=updated_membership
        )


##########################################################
# delete workspace membership
##########################################################


async def test_delete_workspace_membership_self_not_owner_ok():
    workspace = f.build_workspace()
    user = f.build_user()
    general_role = f.build_workspace_role(workspace=workspace, is_owner=False)
    membership = f.build_workspace_membership(
        user=user, workspace=workspace, role=general_role
    )
    with (
        patch(
            "workspaces.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "workspaces.memberships.services.workspace_invitations_repositories",
            autospec=True,
        ) as fake_workspace_invitations_repository,
        patch(
            "workspaces.memberships.services._delete_inner_projects_membership",
            autospec=True,
        ) as fake_delete_inner_projects_membership,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
    ):
        fake_membership_repository.exists_membership.return_value = False
        fake_membership_repository.delete_memberships.return_value = 1
        fake_workspace_invitations_repository.invitation_username_or_email_query.return_value = None
        await services.delete_workspace_membership(
            membership=membership, user=membership.user
        )
        fake_delete_inner_projects_membership.assert_awaited_once_with(membership)
        fake_membership_repository.delete_memberships.assert_awaited_once_with(
            WorkspaceMembership, {"id": membership.id}
        )
        fake_workspace_invitations_repository.delete_invitation.assert_awaited_once_with(
            WorkspaceInvitation,
            filters={
                "workspace_id": workspace.id,
            },
            q_filter=None,
        )
        fake_membership_events.emit_event_when_workspace_membership_is_deleted.assert_awaited_once_with(
            membership=membership
        )


async def test_delete_workspace_membership_self_only_one_owner_without_successor():
    workspace = f.build_workspace()
    owner_role = f.build_workspace_role(workspace=workspace, is_owner=True)
    membership = f.build_workspace_membership(
        user=workspace.created_by, workspace=workspace, role=owner_role
    )
    with (
        patch(
            "workspaces.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "workspaces.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
        pytest.raises(ex.MembershipIsTheOnlyOwnerError),
    ):
        fake_membership_service.is_membership_the_only_owner.return_value = True

        await services.delete_workspace_membership(
            membership=membership, user=membership.user
        )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_membership_repository.delete_memberships.assert_not_awaited()
        fake_membership_events.emit_event_when_workspace_membership_is_deleted.assert_not_awaited()


async def test_delete_workspace_membership_self_only_one_owner_bad_successor():
    workspace = f.build_workspace()
    owner_role = f.build_workspace_role(workspace=workspace, is_owner=True)
    membership = f.build_workspace_membership(
        user=workspace.created_by, workspace=workspace, role=owner_role
    )
    with (
        patch(
            "workspaces.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "workspaces.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
        pytest.raises(ex.MembershipIsTheOnlyOwnerError),
    ):
        fake_membership_service.is_membership_the_only_owner.return_value = True
        fake_membership_repository.get_membership.side_effect = (
            WorkspaceMembership.DoesNotExist
        )

        await services.delete_workspace_membership(
            membership=membership,
            user=membership.user,
            successor_user_id=NOT_EXISTING_UUID,
        )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_membership_repository.delete_memberships.assert_not_awaited()
        fake_membership_events.emit_event_when_workspace_membership_is_deleted.assert_not_awaited()


async def test_delete_workspace_membership_self_only_one_owner_successor_ok():
    workspace = f.build_workspace()
    owner_role = f.build_workspace_role(workspace=workspace, is_owner=True)
    membership = f.build_workspace_membership(
        user=workspace.created_by, workspace=workspace, role=owner_role
    )
    successor = f.build_user()
    successor_membership = f.build_workspace_membership(
        user=successor, workspace=workspace
    )
    with (
        patch(
            "workspaces.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "workspaces.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "workspaces.memberships.services.workspace_invitations_repositories",
            autospec=True,
        ) as fake_workspace_invitations_repository,
        patch(
            "workspaces.memberships.services._delete_inner_projects_membership",
            autospec=True,
        ) as fake_delete_inner_projects_membership,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch(
            "workspaces.memberships.services.update_workspace_membership", autospec=True
        ) as fake_update_workspace_membership,
        patch_db_transaction(),
    ):
        fake_membership_repository.exists_membership.return_value = False
        fake_membership_repository.delete_memberships.return_value = 1
        fake_workspace_invitations_repository.invitation_username_or_email_query.return_value = None
        fake_membership_service.is_membership_the_only_owner.return_value = True
        fake_membership_repository.get_membership.return_value = successor_membership

        await services.delete_workspace_membership(
            membership=membership,
            user=membership.user,
            successor_user_id=NOT_EXISTING_UUID,
        )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_update_workspace_membership.assert_awaited_once_with(
            successor_membership, owner_role.id, user=membership.user
        )
        fake_delete_inner_projects_membership.assert_awaited_once_with(membership)
        fake_membership_repository.delete_memberships.assert_awaited_once_with(
            WorkspaceMembership, {"id": membership.id}
        )
        fake_workspace_invitations_repository.delete_invitation.assert_awaited_once()
        fake_membership_events.emit_event_when_workspace_membership_is_deleted.assert_awaited_once()


async def test_delete_workspace_membership_self_existing_projects():
    workspace = f.build_workspace()
    owner_role = f.build_workspace_role(workspace=workspace, is_owner=True)
    membership = f.build_workspace_membership(
        user=workspace.created_by, workspace=workspace, role=owner_role
    )
    with (
        patch(
            "workspaces.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "workspaces.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
        pytest.raises(ex.ExistingProjectMembershipsError),
    ):
        fake_membership_service.is_membership_the_only_owner.return_value = False
        fake_membership_repository.exists_membership.return_value = True

        await services.delete_workspace_membership(
            membership=membership, user=membership.user
        )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_membership_repository.exists_membership.assert_awaited_once_with(
            ProjectMembership,
            filters={
                "user": membership.user,
                "project__workspace_id": membership.workspace_id,
            },
        )
        fake_membership_repository.delete_memberships.assert_not_awaited()
        fake_membership_events.emit_event_when_workspace_membership_is_deleted.assert_not_awaited()


async def test_delete_workspace_membership_other_no_existing_projects_ok():
    workspace = f.build_workspace()
    owner_role = f.build_workspace_role(workspace=workspace, is_owner=True)
    membership = f.build_workspace_membership(
        user=workspace.created_by, workspace=workspace, role=owner_role
    )
    other_user = f.build_user()
    with (
        patch(
            "workspaces.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "workspaces.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "workspaces.memberships.services.workspace_invitations_repositories",
            autospec=True,
        ) as fake_workspace_invitations_repository,
        patch(
            "workspaces.memberships.services._delete_inner_projects_membership",
            autospec=True,
        ) as fake_delete_inner_projects_membership,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
    ):
        fake_membership_repository.exists_membership.return_value = False
        fake_membership_repository.delete_memberships.return_value = 1
        fake_workspace_invitations_repository.invitation_username_or_email_query.return_value = None
        fake_membership_service.is_membership_the_only_owner.return_value = False
        fake_membership_repository.only_owner_queryset.return_value.values.return_value.__aiter__.return_value = []

        await services.delete_workspace_membership(
            membership=membership, user=other_user
        )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_membership_repository.exists_membership.assert_not_awaited()
        fake_membership_repository.only_owner_queryset.assert_called_once_with(
            Project, membership.user, filters={"workspace_id": membership.workspace_id}
        )
        fake_membership_repository.bulk_update_or_create_memberships.assert_not_awaited()
        fake_delete_inner_projects_membership.assert_awaited_once_with(membership)
        fake_membership_repository.delete_memberships.assert_awaited_once_with(
            WorkspaceMembership, {"id": membership.id}
        )
        fake_workspace_invitations_repository.delete_invitation.assert_awaited_once()
        fake_membership_events.emit_event_when_workspace_membership_is_deleted.assert_awaited_once()


async def test_delete_workspace_membership_other_existing_projects_and_owner_ok():
    workspace = f.build_workspace()
    owner_role = f.build_workspace_role(workspace=workspace, is_owner=True)
    membership = f.build_workspace_membership(
        user=workspace.created_by, workspace=workspace, role=owner_role
    )
    other_user = f.build_user()
    other_user.workspace_role = owner_role
    project = f.build_project(workspace=workspace)
    owner_role = f.build_project_role(project=project, is_owner=True)
    with (
        patch(
            "workspaces.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "workspaces.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "workspaces.memberships.services.workspace_invitations_repositories",
            autospec=True,
        ) as fake_workspace_invitations_repository,
        patch(
            "workspaces.memberships.services._delete_inner_projects_membership",
            autospec=True,
        ) as fake_delete_inner_projects_membership,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
    ):
        fake_membership_repository.exists_membership.return_value = False
        fake_membership_repository.delete_memberships.return_value = 1
        fake_workspace_invitations_repository.invitation_username_or_email_query.return_value = None
        fake_membership_service.is_membership_the_only_owner.return_value = False
        fake_membership_repository.only_owner_queryset.return_value.values.return_value.__aiter__.return_value = [
            {"id": project.id, "memberships__role_id": owner_role.id}
        ]

        await services.delete_workspace_membership(
            membership=membership, user=other_user
        )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_membership_repository.exists_membership.assert_not_awaited()
        fake_membership_repository.only_owner_queryset.assert_called_once_with(
            Project, membership.user, filters={"workspace_id": membership.workspace_id}
        )
        fake_membership_repository.bulk_update_or_create_memberships.assert_awaited_once()
        fake_delete_inner_projects_membership.assert_awaited_once_with(membership)
        fake_membership_repository.delete_memberships.assert_awaited_once_with(
            WorkspaceMembership, {"id": membership.id}
        )
        fake_workspace_invitations_repository.delete_invitation.assert_awaited_once()
        fake_membership_events.emit_event_when_workspace_membership_is_deleted.assert_awaited_once()


async def test_delete_workspace_membership_other_existing_projects_and_not_owner():
    workspace = f.build_workspace()
    owner_role = f.build_workspace_role(workspace=workspace, is_owner=True)
    general_role = f.build_workspace_role(workspace=workspace, is_owner=False)
    membership = f.build_workspace_membership(
        user=workspace.created_by, workspace=workspace, role=owner_role
    )
    other_user = f.build_user()
    other_user.workspace_role = general_role
    project = f.build_project(workspace=workspace)
    owner_role = f.build_project_role(project=project, is_owner=True)
    with (
        patch(
            "workspaces.memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
        patch(
            "workspaces.memberships.services.memberships_services", autospec=True
        ) as fake_membership_service,
        patch(
            "workspaces.memberships.services.memberships_events", autospec=True
        ) as fake_membership_events,
        patch_db_transaction(),
        pytest.raises(ex.ExistingOwnerProjectMembershipsAndNotOwnerError),
    ):
        fake_membership_service.is_membership_the_only_owner.return_value = False
        fake_membership_repository.only_owner_queryset.return_value.values.return_value.__aiter__.return_value = [
            {"id": project.id, "memberships__role_id": owner_role.id}
        ]

        await services.delete_workspace_membership(
            membership=membership, user=other_user
        )
        fake_membership_service.is_membership_the_only_owner.assert_awaited_once_with(
            membership
        )
        fake_membership_repository.exists_membership.assert_not_awaited()
        fake_membership_repository.only_owner_queryset.assert_called_once_with(
            Project, membership.user, filters={"workspace_id": membership.workspace_id}
        )
        fake_membership_repository.delete_memberships.assert_not_awaited()
        fake_membership_events.emit_event_when_workspace_membership_is_deleted.assert_not_awaited()


#######################################################
# misc is_membership_the_only_owner
#######################################################


async def test_is_workspace_membership_the_only_owner_not_owner_role():
    role = f.build_workspace_role(is_owner=False)
    membership = f.build_workspace_membership(role=role)
    with (
        patch(
            "memberships.services.memberships_repositories", autospec=True
        ) as fake_membership_repository,
    ):
        assert not await services.is_membership_the_only_owner(membership)
        fake_membership_repository.has_other_owner_memberships.assert_not_called()


async def test_is_workspace_membership_the_only_owner_true():
    role = f.build_workspace_role(is_owner=True)
    membership = f.build_workspace_membership(role=role)
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


async def test_is_workspace_membership_the_only_owner_false():
    role = f.build_workspace_role(is_owner=True)
    membership = f.build_workspace_membership(role=role)
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
# list_workspace_role
##########################################################


async def test_list_workspace_role():
    workspace = f.build_workspace()
    role = f.build_workspace_role(workspace=workspace)
    with (
        patch(
            "workspaces.memberships.services.memberships_repositories",
            autospec=True,
        ) as fake_ws_memberships_repo,
    ):
        fake_ws_memberships_repo.list_roles.return_value = [role]
        ret = await services.list_workspace_roles(workspace)

        fake_ws_memberships_repo.list_roles.assert_awaited_once_with(
            WorkspaceRole,
            filters={"workspace_id": workspace.id},
            get_total_members=True,
        )
        assert ret == [role]


##########################################################
# get_workspace_role
##########################################################


async def test_get_workspace_role():
    workspace = f.build_workspace()
    role = f.build_workspace_role(workspace=workspace)
    with (
        patch(
            "workspaces.memberships.services.memberships_repositories",
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

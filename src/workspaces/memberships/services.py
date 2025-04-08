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

from uuid import UUID

from memberships import services as memberships_services
from memberships.services import exceptions as ex
from memberships.services import has_permission, is_membership_the_only_owner  # noqa
from workspaces.invitations import repositories as workspace_invitations_repositories
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships import events as memberships_events
from workspaces.memberships import repositories as memberships_repositories
from workspaces.memberships.models import WorkspaceMembership, WorkspaceRole
from workspaces.workspaces.models import Workspace

##########################################################
# list workspace memberships
##########################################################


async def list_workspace_memberships(workspace: Workspace) -> list[WorkspaceMembership]:
    return await memberships_repositories.list_memberships(
        WorkspaceMembership,
        filters={"workspace_id": workspace.id},
        select_related=["user", "role", "workspace"],
    )


##########################################################
# get workspace membership
##########################################################


async def get_workspace_membership(
    workspace_id: UUID,
    username: str,
) -> WorkspaceMembership | None:
    return await memberships_repositories.get_membership(
        WorkspaceMembership,
        filters={"workspace_id": workspace_id, "user__username": username},
        select_related=["workspace", "user", "role"],
    )


##########################################################
# update workspace membership
##########################################################


async def update_workspace_membership(
    membership: WorkspaceMembership, role_slug: str
) -> WorkspaceMembership:
    try:
        workspace_role = await memberships_repositories.get_role(
            WorkspaceRole,
            filters={"workspace_id": membership.workspace_id, "slug": role_slug},
        )

    except WorkspaceRole.DoesNotExist as e:
        raise ex.NonExistingRoleError("Role does not exist") from e

    if not workspace_role.is_owner:
        if await memberships_services.is_membership_the_only_owner(membership):
            raise ex.MembershipIsTheOnlyOwnerError("Membership is the only owner")

    updated_membership = await memberships_repositories.update_membership(
        membership=membership,
        values={"role": workspace_role},
    )

    await memberships_events.emit_event_when_workspace_membership_is_updated(
        membership=updated_membership
    )

    return updated_membership


##########################################################
# delete workspace membership
##########################################################


async def delete_workspace_membership(
    membership: WorkspaceMembership,
) -> bool:
    if await memberships_services.is_membership_the_only_owner(membership):
        raise ex.MembershipIsTheOnlyOwnerError("Membership is the only owner")

    deleted = await memberships_repositories.delete_membership(membership)
    if deleted > 0:
        # Delete workspace invitations
        await workspace_invitations_repositories.delete_invitation(
            WorkspaceInvitation,
            filters={
                "workspace_id": membership.workspace_id,
            },
            q_filter=workspace_invitations_repositories.username_or_email_query(
                membership.user.email
            ),
        )
        await memberships_events.emit_event_when_workspace_membership_is_deleted(
            membership=membership
        )
        return True

    return False


##########################################################
# list workspace roles
##########################################################


async def list_workspace_roles(workspace: Workspace) -> list[WorkspaceRole]:
    return await memberships_repositories.list_roles(
        WorkspaceRole, filters={"workspace_id": workspace.id}
    )


##########################################################
# get workspace role
##########################################################


async def get_workspace_role(workspace_id: UUID, slug: str) -> WorkspaceRole:
    return await memberships_repositories.get_role(
        WorkspaceRole,
        filters={"workspace_id": workspace_id, "slug": slug},
        select_related=["workspace"],
    )
